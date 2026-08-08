"""
PayPal Developer Sandbox Integration
This module provides integration with PayPal's sandbox environment for testing payments.
"""

import os
from paypalrestsdk import Api, Payment, Sale, Refund
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PayPalSandboxIntegration:
    """PayPal Sandbox integration class for handling payments and transactions."""
    
    def __init__(self, client_id=None, client_secret=None, mode='sandbox'):
        """
        Initialize PayPal API with sandbox credentials.
        
        Args:
            client_id (str): PayPal Client ID from Developer Dashboard
            client_secret (str): PayPal Client Secret from Developer Dashboard
            mode (str): 'sandbox' for testing, 'live' for production
        """
        self.client_id = client_id or os.getenv('PAYPAL_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('PAYPAL_CLIENT_SECRET')
        self.mode = mode
        
        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal Client ID and Secret are required")
        
        # Configure PayPal API
        self.api = Api({
            'mode': self.mode,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        })
        
        logger.info(f"PayPal API initialized in {self.mode} mode")
    
    def create_payment(self, amount, currency='USD', description='', return_url='', cancel_url=''):
        """
        Create a payment in sandbox environment.
        
        Args:
            amount (str): Payment amount
            currency (str): Currency code (default: USD)
            description (str): Payment description
            return_url (str): URL to return to after approval
            cancel_url (str): URL if payment is canceled
            
        Returns:
            dict: Payment details including approval URL
        """
        try:
            payment = Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": return_url or "http://localhost:3000/payment/execute",
                    "cancel_url": cancel_url or "http://localhost:3000/payment/cancel"
                },
                "transactions": [{
                    "amount": {
                        "total": amount,
                        "currency": currency,
                        "details": {
                            "subtotal": amount
                        }
                    },
                    "description": description,
                    "invoice_number": self._generate_invoice_number()
                }]
            })
            
            if payment.create():
                logger.info(f"Payment created successfully: {payment.id}")
                
                # Get approval URL
                approval_url = next(
                    (link['href'] for link in payment.links if link['rel'] == 'approval_url'),
                    None
                )
                
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'approval_url': approval_url,
                    'status': payment.state
                }
            else:
                logger.error(f"Payment creation failed: {payment.error}")
                return {
                    'success': False,
                    'error': payment.error
                }
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_payment(self, payment_id, payer_id):
        """
        Execute an approved payment.
        
        Args:
            payment_id (str): Payment ID from PayPal
            payer_id (str): Payer ID from PayPal redirect
            
        Returns:
            dict: Execution result with transaction details
        """
        try:
            payment = Payment.find(payment_id)
            
            if payment.execute({"payer_id": payer_id}):
                logger.info(f"Payment executed successfully: {payment_id}")
                return {
                    'success': True,
                    'payment_id': payment.id,
                    'status': payment.state,
                    'transactions': payment.transactions
                }
            else:
                logger.error(f"Payment execution failed: {payment.error}")
                return {
                    'success': False,
                    'error': payment.error
                }
        except Exception as e:
            logger.error(f"Error executing payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def refund_payment(self, sale_id, amount=None):
        """
        Refund a completed payment.
        
        Args:
            sale_id (str): Sale ID from completed transaction
            amount (str): Refund amount (None for full refund)
            
        Returns:
            dict: Refund result
        """
        try:
            sale = Sale.find(sale_id)
            
            refund_dict = {}
            if amount:
                refund_dict['amount'] = {
                    'currency': 'USD',
                    'total': amount
                }
            
            if sale.refund(refund_dict):
                logger.info(f"Refund successful for sale: {sale_id}")
                return {
                    'success': True,
                    'refund_id': sale.refund['id'],
                    'status': sale.refund['state']
                }
            else:
                logger.error(f"Refund failed: {sale.error}")
                return {
                    'success': False,
                    'error': sale.error
                }
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_details(self, payment_id):
        """
        Retrieve details of a specific payment.
        
        Args:
            payment_id (str): Payment ID
            
        Returns:
            dict: Payment details
        """
        try:
            payment = Payment.find(payment_id)
            return {
                'success': True,
                'payment_id': payment.id,
                'status': payment.state,
                'amount': payment.transactions[0]['amount'] if payment.transactions else None,
                'created_time': payment.create_time,
                'updated_time': payment.update_time
            }
        except Exception as e:
            logger.error(f"Error retrieving payment details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _generate_invoice_number():
        """Generate a unique invoice number."""
        from datetime import datetime
        import random
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_num = random.randint(1000, 9999)
        return f"INV-{timestamp}-{random_num}"


# Example usage
if __name__ == "__main__":
    # Initialize PayPal Sandbox
    paypal = PayPalSandboxIntegration()
    
    # Create a payment
    print("Creating payment...")
    payment_result = paypal.create_payment(
        amount="25.00",
        currency="USD",
        description="Test Payment",
        return_url="http://localhost:3000/payment/execute",
        cancel_url="http://localhost:3000/payment/cancel"
    )
    
    if payment_result['success']:
        print(f"Payment ID: {payment_result['payment_id']}")
        print(f"Approval URL: {payment_result['approval_url']}")
    else:
        print(f"Error: {payment_result['error']}")
