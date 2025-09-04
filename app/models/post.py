from app.extensions import db


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "userId": self.userId, "title": self.title, "body": self.body}
