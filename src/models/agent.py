from src.models.user import db
import uuid
import datetime

class Agent(db.Model):
    __tablename__ = 'agents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    unique_key = db.Column(db.String(36), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(20), default='offline')  # online, offline
    available_components = db.Column(db.Text)  # JSON string of available components
    
    def __repr__(self):
        return f'<Agent {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unique_key': self.unique_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'status': self.status,
            'available_components': self.available_components
        }

class Metrics(db.Model):
    __tablename__ = 'metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(36), db.ForeignKey('agents.id'), nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # cpu, memory, disk, network, processes, uptime, docker
    metric_data = db.Column(db.Text, nullable=False)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    agent = db.relationship('Agent', backref=db.backref('metrics', lazy=True))
    
    def __repr__(self):
        return f'<Metrics {self.metric_type} for {self.agent_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'metric_type': self.metric_type,
            'metric_data': self.metric_data,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

