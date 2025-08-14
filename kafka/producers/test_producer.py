#!/usr/bin/env python3
"""
Kafka Test Producer for Insurance Platform

This script generates and publishes test insurance events to Kafka topics
for testing streaming data processing capabilities.
"""

import json
import random
import time
import uuid
from datetime import datetime, timedelta
from kafka import KafkaProducer
from faker import Faker
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker('en_US')
Faker.seed(42)

class InsuranceEventProducer:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: str(k).encode('utf-8'),
            acks='all',
            retries=3,
            retry_backoff_ms=1000,
            max_in_flight_requests_per_connection=1
        )
        
        self.policy_types = ['auto', 'home', 'life', 'health']
        self.claim_types = {
            'auto': ['accident', 'theft', 'vandalism', 'collision'],
            'home': ['fire', 'theft', 'storm', 'water_damage'],
            'life': ['death_benefit', 'disability'], 
            'health': ['medical_expense', 'prescription', 'emergency']
        }
        self.policy_statuses = ['active', 'inactive', 'cancelled', 'expired']
        self.claim_statuses = ['open', 'investigating', 'approved', 'denied', 'closed']
        self.payment_statuses = ['pending', 'completed', 'failed', 'refunded']
        
    def generate_policy_event(self):
        """Generate a policy-related event"""
        policy_type = random.choice(self.policy_types)
        
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': random.choice(['policy_created', 'policy_updated', 'policy_renewed', 'policy_cancelled']),
            'timestamp': datetime.now().isoformat(),
            'policy_id': str(uuid.uuid4()),
            'policy_number': f"POL{random.randint(10000000, 99999999)}",
            'customer_id': str(uuid.uuid4()),
            'policy_type': policy_type,
            'policy_status': random.choice(self.policy_statuses),
            'premium_amount': round(random.uniform(500, 5000), 2),
            'coverage_amount': round(random.uniform(25000, 1000000), 2),
            'effective_date': (datetime.now() - timedelta(days=random.randint(0, 365))).date().isoformat(),
            'expiration_date': (datetime.now() + timedelta(days=random.randint(1, 365))).date().isoformat(),
            'agent_id': str(uuid.uuid4()),
            'territory': random.choice(['North', 'South', 'East', 'West', 'Central']),
            'source_system': 'PMS',
            'metadata': {
                'version': '1.0',
                'correlation_id': str(uuid.uuid4()),
                'producer': 'test_producer'
            }
        }
        
        return event
    
    def generate_claim_event(self):
        """Generate a claim-related event"""
        policy_type = random.choice(self.policy_types)
        claim_type = random.choice(self.claim_types[policy_type])
        
        incident_date = datetime.now() - timedelta(days=random.randint(1, 90))
        reported_date = incident_date + timedelta(days=random.randint(0, 30))
        
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': random.choice(['claim_submitted', 'claim_updated', 'claim_approved', 'claim_denied', 'claim_settled']),
            'timestamp': datetime.now().isoformat(),
            'claim_id': str(uuid.uuid4()),
            'claim_number': f"CLM{random.randint(10000000, 99999999)}",
            'policy_id': str(uuid.uuid4()),
            'policy_type': policy_type,
            'claim_type': claim_type,
            'claim_status': random.choice(self.claim_statuses),
            'incident_date': incident_date.date().isoformat(),
            'reported_date': reported_date.date().isoformat(),
            'claim_amount': round(random.uniform(1000, 50000), 2),
            'settlement_amount': round(random.uniform(800, 45000), 2) if random.random() > 0.3 else None,
            'adjuster_id': str(uuid.uuid4()),
            'incident_location': f"{fake.city()}, {fake.state_abbr()}",
            'description': fake.text(max_nb_chars=200),
            'source_system': 'CMS',
            'metadata': {
                'version': '1.0',
                'correlation_id': str(uuid.uuid4()),
                'producer': 'test_producer',
                'priority': random.choice(['low', 'medium', 'high'])
            }
        }
        
        return event
    
    def generate_payment_event(self):
        """Generate a payment-related event"""
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': random.choice(['payment_initiated', 'payment_completed', 'payment_failed', 'payment_refunded']),
            'timestamp': datetime.now().isoformat(),
            'payment_id': str(uuid.uuid4()),
            'policy_id': str(uuid.uuid4()),
            'transaction_id': f"TXN{uuid.uuid4().hex[:12].upper()}",
            'payment_method': random.choice(['credit_card', 'bank_transfer', 'check', 'digital_wallet']),
            'payment_amount': round(random.uniform(100, 1000), 2),
            'payment_date': datetime.now().date().isoformat(),
            'payment_status': random.choice(self.payment_statuses),
            'billing_period_start': (datetime.now() - timedelta(days=30)).date().isoformat(),
            'billing_period_end': datetime.now().date().isoformat(),
            'customer_id': str(uuid.uuid4()),
            'source_system': 'BILLING',
            'metadata': {
                'version': '1.0',
                'correlation_id': str(uuid.uuid4()),
                'producer': 'test_producer',
                'payment_processor': random.choice(['stripe', 'paypal', 'square'])
            }
        }
        
        return event
    
    def generate_customer_event(self):
        """Generate a customer-related event"""
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': random.choice(['customer_created', 'customer_updated', 'customer_profile_changed']),
            'timestamp': datetime.now().isoformat(),
            'customer_id': str(uuid.uuid4()),
            'customer_type': random.choice(['individual', 'business']),
            'email': fake.email(),
            'phone': fake.phone_number(),
            'address': {
                'street': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip_code': fake.zipcode()
            },
            'risk_score': round(random.uniform(1.0, 10.0), 2),
            'total_policies': random.randint(1, 5),
            'total_premium': round(random.uniform(1000, 10000), 2),
            'customer_since': (datetime.now() - timedelta(days=random.randint(30, 3650))).date().isoformat(),
            'source_system': 'CRM',
            'metadata': {
                'version': '1.0',
                'correlation_id': str(uuid.uuid4()),
                'producer': 'test_producer',
                'channel': random.choice(['web', 'mobile', 'agent', 'call_center'])
            }
        }
        
        return event
    
    def generate_agent_activity_event(self):
        """Generate an agent activity event"""
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': random.choice(['policy_sold', 'quote_generated', 'customer_contacted', 'claim_assigned']),
            'timestamp': datetime.now().isoformat(),
            'agent_id': str(uuid.uuid4()),
            'employee_id': f"EMP{random.randint(10000, 99999)}",
            'customer_id': str(uuid.uuid4()),
            'policy_id': str(uuid.uuid4()) if random.random() > 0.3 else None,
            'activity_details': {
                'duration_minutes': random.randint(5, 120),
                'outcome': random.choice(['successful', 'pending', 'unsuccessful']),
                'notes': fake.sentence()
            },
            'territory': random.choice(['North', 'South', 'East', 'West', 'Central']),
            'commission_amount': round(random.uniform(50, 500), 2) if random.random() > 0.5 else None,
            'source_system': 'AGENT_PORTAL',
            'metadata': {
                'version': '1.0',
                'correlation_id': str(uuid.uuid4()),
                'producer': 'test_producer',
                'location': f"{fake.city()}, {fake.state_abbr()}"
            }
        }
        
        return event
    
    def send_event(self, topic, event, key=None):
        """Send event to Kafka topic"""
        try:
            future = self.producer.send(
                topic,
                value=event,
                key=key or event.get('event_id')
            )
            
            # Wait for the message to be sent
            record_metadata = future.get(timeout=10)
            
            logger.debug(f"Event sent to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event to {topic}: {str(e)}")
            return False
    
    def produce_test_data(self, duration_minutes=10, events_per_minute=60):
        """Produce test events for specified duration"""
        logger.info(f"Starting test data production for {duration_minutes} minutes at {events_per_minute} events/minute")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        events_sent = 0
        events_failed = 0
        
        event_generators = [
            ('policy-events', self.generate_policy_event, 0.3),
            ('claim-events', self.generate_claim_event, 0.25),
            ('payment-events', self.generate_payment_event, 0.25),
            ('customer-events', self.generate_customer_event, 0.1),
            ('agent-activities', self.generate_agent_activity_event, 0.1)
        ]
        
        try:
            while datetime.now() < end_time:
                minute_start = datetime.now()
                minute_events = 0
                
                while minute_events < events_per_minute and datetime.now() < minute_start + timedelta(minutes=1):
                    # Select event type based on weights
                    rand = random.random()
                    cumulative_weight = 0
                    
                    for topic, generator, weight in event_generators:
                        cumulative_weight += weight
                        if rand <= cumulative_weight:
                            event = generator()
                            
                            if self.send_event(topic, event):
                                events_sent += 1
                            else:
                                events_failed += 1
                            
                            minute_events += 1
                            break
                    
                    # Small delay to distribute events throughout the minute
                    time.sleep(60.0 / events_per_minute)
                
                if minute_events > 0:
                    logger.info(f"Sent {minute_events} events in the last minute. Total sent: {events_sent}, failed: {events_failed}")
                
                # Sleep remainder of minute if we finished early
                remaining_time = 60 - (datetime.now() - minute_start).total_seconds()
                if remaining_time > 0:
                    time.sleep(remaining_time)
        
        except KeyboardInterrupt:
            logger.info("Production stopped by user")
        
        except Exception as e:
            logger.error(f"Error during production: {str(e)}")
        
        finally:
            self.producer.flush()
            self.producer.close()
            
            logger.info(f"Production completed. Total events sent: {events_sent}, failed: {events_failed}")
    
    def produce_batch_events(self, event_count=1000):
        """Produce a batch of test events quickly"""
        logger.info(f"Producing {event_count} test events...")
        
        events_sent = 0
        events_failed = 0
        
        event_generators = [
            ('policy-events', self.generate_policy_event, 300),
            ('claim-events', self.generate_claim_event, 250),
            ('payment-events', self.generate_payment_event, 250),
            ('customer-events', self.generate_customer_event, 100),
            ('agent-activities', self.generate_agent_activity_event, 100)
        ]
        
        try:
            for topic, generator, count in event_generators:
                topic_events = min(count, event_count - events_sent)
                
                for _ in range(topic_events):
                    event = generator()
                    
                    if self.send_event(topic, event):
                        events_sent += 1
                    else:
                        events_failed += 1
                    
                    if events_sent >= event_count:
                        break
                
                logger.info(f"Sent {topic_events} events to {topic}")
                
                if events_sent >= event_count:
                    break
        
        except Exception as e:
            logger.error(f"Error during batch production: {str(e)}")
        
        finally:
            self.producer.flush()
            self.producer.close()
            
            logger.info(f"Batch production completed. Events sent: {events_sent}, failed: {events_failed}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Insurance Kafka Test Producer')
    parser.add_argument('--mode', choices=['stream', 'batch'], default='batch',
                       help='Production mode: stream for continuous, batch for one-time')
    parser.add_argument('--duration', type=int, default=10,
                       help='Duration in minutes for stream mode (default: 10)')
    parser.add_argument('--rate', type=int, default=60,
                       help='Events per minute for stream mode (default: 60)')
    parser.add_argument('--count', type=int, default=1000,
                       help='Number of events for batch mode (default: 1000)')
    parser.add_argument('--servers', default='localhost:9092',
                       help='Kafka bootstrap servers (default: localhost:9092)')
    
    args = parser.parse_args()
    
    # Initialize producer
    producer = InsuranceEventProducer(args.servers.split(','))
    
    try:
        if args.mode == 'stream':
            producer.produce_test_data(args.duration, args.rate)
        else:
            producer.produce_batch_events(args.count)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Production failed: {str(e)}")

if __name__ == "__main__":
    main()