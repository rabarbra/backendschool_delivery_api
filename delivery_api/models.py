# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


regions = db.Table("regions",
                   db.Column('region_id',
                             db.Integer,
                             db.ForeignKey('region.id'),
                             primary_key=True),
                   db.Column('courier_id',
                             db.Integer,
                             db.ForeignKey('courier.courier_id'),
                             primary_key=True),
                   )


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orders = db.relationship('Order', backref='regions', lazy=True)

    def __init__(self, id):
        self.id = id
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"

    def create_or_return(regions):
        res = []
        for region in regions:
            reg = Region.query.filter(Region.id == region).first()
            if reg:
                res.append(reg)
            else:
                res.append(Region(region))
        return(res)


class Courier(db.Model):

    courier_id = db.Column(db.Integer, primary_key=True)
    courier_type = db.Column(db.String(5), nullable=False)
    regions = db.relationship('Region', secondary=regions, lazy='subquery',
                              backref=db.backref('couriers', lazy=True))
    working_hours = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Numeric(precision=2))
    earning = db.Column(db.Integer, default=0)
    orders = db.relationship("Order", backref="courier", lazy=True)
    prev_order_time = db.Column(db.DateTime)

    def __init__(self, courier_id, courier_type, regions, working_hours):
        self.courier_id = courier_id
        self.courier_type = courier_type
        self.regions = Region.create_or_return(regions)
        self.working_hours = " ".join(working_hours)
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.courier_id}>"

    def get_regions(self):
        return [region.id for region in self.regions]

    def compute_rating(self):
        sql = f'SELECT MIN(a) FROM ' \
               '(SELECT AVG(o.delivery_time) AS a ' \
               'FROM "order" AS o ' \
               'WHERE o.courier_id = {self.courier_id} ' \
               'AND o.delivery_time IS NOT NULL ' \
               'GROUP BY o.region)'
        min_time = int(db.session.execute(sql).first()[0])
        if not min_time:
            return
        rating = round((3600 - min(min_time, 3600)) / 720, 2)
        self.rating = rating
        db.session.commit()


class Order(db.Model):

    order_id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Numeric(precision=2), nullable=False)
    region = db.Column(db.Integer, db.ForeignKey('region.id'), nullable=False)
    delivery_hours = db.Column(db.String(250), nullable=False)
    assign_time = db.Column(db.DateTime)
    complete_time = db.Column(db.DateTime)
    delivery_time = db.Column(db.Integer)
    courier_id = db.Column(db.Integer, db.ForeignKey('courier.courier_id'))

    def __init__(self, order_id, weight, region, delivery_hours):
        self.order_id = order_id
        self.weight = weight
        self.region = region
        self.delivery_hours = " ".join(delivery_hours)
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.order_id}>"

    def withdraw(self):
        self.assign_time = None
        self.courier_id = None
        db.session.commit()
