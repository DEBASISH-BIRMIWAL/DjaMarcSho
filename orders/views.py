from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import OrderItem, Order
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import order_created
from django.http import HttpResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_pdf(order):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, f"Invoice for Order #{order.id}")

    p.setFont("Helvetica", 12)
    p.drawString(100, 730, f"Invoice No: {order.id}")
    p.drawString(100, 710, f"Date: {order.created.strftime('%b %d, %Y')}")

    # Billing Information
    p.drawString(100, 680, "Bill to:")
    p.drawString(100, 660, f"{order.first_name} {order.last_name}")
    p.drawString(100, 640, order.email)
    p.drawString(100, 620, order.address)
    p.drawString(100, 600, f"{order.postal_code}, {order.city}")

    # Items
    p.drawString(100, 570, "Items bought:")
    p.drawString(100, 550, "Product       Price       Quantity       Cost")
    p.drawString(100, 540, "-" * 60)

    y_position = 520
    for item in order.items.all():  # Use the related name 'items'
        cost = item.get_cost()
        p.drawString(100, y_position, f"{item.product.name}       ${item.price:.2f}       {item.quantity}       ${cost:.2f}")
        y_position -= 20

    # Total Cost
    total_cost = order.get_total_cost()
    p.drawString(100, y_position, f"Total: ${total_cost:.2f}")

    # Payment Status
    payment_status = "Paid" if order.paid else "Pending payment"
    p.drawString(100, y_position - 20, f"Status: {payment_status}")

    # Finalize PDF
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order,
                                         product=item['product'],
                                         price=item['price'],
                                         quantity=item['quantity'])
            cart.clear()
            order_created.delay(order.id)
            request.session['order_id'] = order.id
            return redirect(reverse('payment:process'))
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order/create.html', {'cart': cart, 'form': form})

@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/orders/order/detail.html', {'order': order})

@staff_member_required
def admin_order_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    pdf_buffer = generate_pdf(order)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=order_{order.id}.pdf'
    return response
