# -*- coding: utf-8 -*-
from datetime import time
from marshmallow import Schema, fields, validate, post_load, ValidationError
from marshmallow.utils import get_value
from .models import Courier, Order


def validate_time(value):
    if "-" not in value:
        raise ValidationError("Time separator '-' not present.")
    times = value.split("-")
    if len(times) != 2:
        raise ValidationError(
                f"Not a valid time interval. {len(times)} values, needs 2.")
    for t in times:
        try:
            time.fromisoformat(t)
        except ValueError:
            raise ValidationError("Not a valid time isoformat.")


class CourierSchema(Schema):
    courier_id = fields.Integer(required=True)
    courier_type = fields.String(
            required=True,
            validate=validate.OneOf(["foot", "bike", "car"]))
    regions = fields.List(
            fields.Int(), required=True,
            validate=validate.Length(min=1))
    working_hours = fields.List(
            fields.String(validate=validate_time), required=True,
            validate=validate.Length(min=1))
    rating = fields.Float()
    earning = fields.Integer()

    @post_load
    def make_courier(self, data, **kwargs):
        return Courier(**data)

    def get_attribute(self, obj, key, default):
        if key == "regions":
            return obj.get_regions()
        elif key == "working_hours":
            return obj.working_hours.split()
        else:
            return get_value(obj, key, default)


class OrderSchema(Schema):
    order_id = fields.Integer(required=True)
    weight = fields.Float(
            required=True,
            validate=validate.Range(min=0.01, max=50))
    region = fields.Integer(
            required=True,
            validate=validate.Range(min=0))
    delivery_hours = fields.List(
            fields.String(validate=validate_time), required=True,
            validate=validate.Length(min=1))

    @post_load
    def new_order(self, data, **kwargs):
        return Order(**data)

    def get_attribute(self, obj, key, default):
        if key == "delivery_hours":
            return obj.delivery_hours.split()
        else:
            return get_value(obj, key, default)
