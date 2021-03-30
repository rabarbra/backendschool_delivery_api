# -*- coding: utf-8 -*-
from datetime import time, datetime
from dateutil import parser, tz
from rfc3339 import rfc3339
from flask import Blueprint, request, jsonify, make_response
from .models import db, Courier, Order, Region
from .schemas import CourierSchema, OrderSchema, ValidationError, validate_time

bp = Blueprint('my_api', __name__, url_prefix='')

couriers_schema = CourierSchema(many=True)
orders_schema = OrderSchema(many=True)
courier_schema = CourierSchema(only=("courier_id", "courier_type", "regions",
                                     "working_hours", "rating", "earning"))
courier_item_schema = CourierSchema(only=("courier_id", "courier_type",
                                          "regions", "working_hours"))
weights = {"foot": 10, "bike": 15, "car": 50}
coeffs = {"foot": 2, "bike": 5, "car": 9}


def are_intersecting(int1, int2):
    int1 = [tuple(time.fromisoformat(i)
            for i in interval.split("-")) for interval in int1.split()]
    int2 = [tuple(time.fromisoformat(i)
            for i in interval.split("-")) for interval in int2.split()]
    for i1 in int1:
        for i2 in int2:
            if i1[0] < i2[1] and i1[1] > i2[0]:
                return True
    return False


@bp.route('/couriers', methods=['POST'], strict_slashes=False)
def post_couriers():
    errors = CourierSchema().validate(request.json["data"], many=True)
    if errors:
        couriers = []
        for key in errors.keys():
            couriers.append({"id": request.json["data"][key]["courier_id"],
                             "errors": errors[key]})
        response = {"validation_error": {"courirers": couriers}}
        return make_response(jsonify(response), 400)
    couriers = couriers_schema.load(request.json["data"])
    ids = []
    for courier in couriers:
        ids.append({"id": courier.courier_id})
    response = {"couriers": ids}
    return make_response(jsonify(response), 201)


@bp.route('/couriers/<int:courier_id>', methods=["PATCH", "GET"])
def path_courier(courier_id):
    courier = Courier.query.filter(Courier.courier_id == courier_id).first()
    if not courier:
        return jsonify("Not found"), 404
    if request.method == "GET":
        response = courier_schema.dump(courier)
        if response["rating"] is None:
            del response["rating"]
        return jsonify(response)
    data = request.json
    orders = [order for order in courier.orders if not order.complete_time]
    for key in data.keys():
        if key not in ["courier_type", "regions", "working_hours"]:
            return jsonify("Bad request"), 400
        if key == "courier_type":
            if data[key] in ["foot", "bike", "car"]:
                courier.courier_type = data[key]
                for order in orders:
                    if order.weight > weights[courier.courier_type]:
                        order.withdraw()
            else:
                return jsonify("Bad request"), 400
        elif key == "regions":
            if len(data[key]) < 1:
                return jsonify("Bad request"), 400
            for reg in data[key]:
                if type(reg) is not int or reg < 0:
                    return jsonify("Bad request"), 400
            courier.regions = Region.create_or_return(data[key])
            for order in orders:
                if order.region not in courier.get_regions():
                    order.withdraw()
        elif key == "working_hours":
            if len(data[key]) < 1:
                return jsonify("Bad request"), 400
            for t in data[key]:
                try:
                    validate_time(t)
                except ValidationError:
                    return jsonify("Bad request"), 400
            courier.working_hours = " ".join(data[key])
            for order in orders:
                if not are_intersecting(order.delivery_hours,
                                        courier.working_hours):
                    order.withdraw()
    db.session.commit()
    return courier_item_schema.dump(courier)


@bp.route('/orders', methods=['POST'], strict_slashes=False)
def post_orders():
    errors = OrderSchema().validate(request.json["data"], many=True)
    if errors:
        orders = []
        for key in errors.keys():
            orders.append({"id": request.json["data"][key]["order_id"],
                           "errors": errors[key]})
        response = {"validation_error": {"orders": orders}}
        return make_response(jsonify(response), 400)
    orders = orders_schema.load(request.json["data"])
    ids = []
    for order in orders:
        ids.append({"id": order.order_id})
    response = {"orders": ids}
    return make_response(jsonify(response), 201)


@bp.route('/orders/assign', methods=['POST'])
def assign_orders():
    courier_id = request.json["courier_id"]
    courier = Courier.query.filter(Courier.courier_id == courier_id).first()
    if not courier:
        return jsonify("Bad request"), 400
    orders = Order.query.filter(
            Order.weight <= weights[courier.courier_type],
            db.text(f'order_region IN '
                    f'({", ".join([str(i)for i in courier.get_regions()])})'),
            db.text('order_courier_id IS NULL')
    ).all()
    now = datetime.utcnow().replace(tzinfo=tz.UTC)
    ids = []
    for order in orders:
        if are_intersecting(order.delivery_hours, courier.working_hours):
            courier.orders.append(order)
            order.assign_time = now
            if not courier.prev_order_time:
                courier.prev_order_time = now
            db.session.commit()
            ids.append({"id": order.order_id})
    if len(ids) == 0:
        response = {"orders": []}
    else:
        response = {"orders": ids, "assign_time": rfc3339(now, utc=True)}
    return jsonify(response)


@bp.route('/orders/complete', methods=['POST'])
def complete_order():
    data = request.json
    order = Order.query.filter(Order.order_id == data["order_id"]).first()
    courier = Courier.query.filter(Courier.courier_id == data["courier_id"])
    courier = courier.first()
    if not order or not courier or order.courier_id != courier.courier_id:
        return jsonify("Bad request"), 404
    if order.complete_time:
        return jsonify({"order_id": order.order_id})
    order.complete_time = parser.parse(data["complete_time"])
    order.delivery_time = int((
        order.complete_time.replace(tzinfo=None) -
        courier.prev_order_time.replace(tzinfo=None)).total_seconds())
    courier.prev_order_time = order.complete_time
    courier.earning += 500 * coeffs[courier.courier_type]
    db.session.commit()
    courier.compute_rating()
    return jsonify({"order_id": order.order_id})
