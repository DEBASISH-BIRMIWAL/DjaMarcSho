from decimal import Decimal
from django.shortcuts import render, redirect, reverse, get_object_or_404
from orders.models import Order
import random  # to simulate success or failure

def payment_process(request):
    order_id = request.session.get('order_id', None)
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        # Simulate payment gateway session data
        success_url = request.build_absolute_uri(reverse('payment:completed'))
        cancel_url = request.build_absolute_uri(reverse('payment:canceled'))

        # Dummy session data - simulate successful or failed payment
        session_data = {
            'mode': 'payment',
            'client_reference_id': order.id,
            'success_url': success_url,
            'cancel_url': cancel_url,
            'line_items': []
        }

        # Add order items to the dummy session data (simulating Stripe behavior)
        for item in order.items.all():
            session_data['line_items'].append({
                'price_data': {
                    'unit_amount': int(item.price * Decimal('100')),  # Convert to cents
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                    },
                },
                'quantity': item.quantity,
            })

        # Simulate random payment outcome (success or failure)
        payment_successful = random.choice([True, False])

        if payment_successful:
            # Redirect to success URL
            return redirect(success_url)
        else:
            # Redirect to canceled URL
            return redirect(cancel_url)

    else:
        return render(request, 'payment/process.html', locals())

def payment_completed(request):
    order_id = request.session.get('order_id', None)
    order = get_object_or_404(Order, id=order_id)

    if not order.paid:
        order.paid = True
        order.save()

    return render(request, 'payment/completed.html')

def payment_canceled(request):
    return render(request, 'payment/canceled.html')

