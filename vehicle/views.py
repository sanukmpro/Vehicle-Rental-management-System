from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render,redirect
import json
from django.http import JsonResponse
from django.http import HttpResponse
from .models import Users,Vehicle,Driver,VehicleBooking,Notification,Bids,DriverRequests
from django.shortcuts import redirect, get_object_or_404
import traceback
from django.contrib import messages
# Create your views here.
def home(request):
    isLoggedIn = False
    isDriver = False
    try:
        isDriver = request.session["is_driver"]
    except:
        isDriver = False
    try:
        isLoggedIn = request.session["logged_in"]
    except:
        isLoggedIn = False
    has_unread_notifications = False
    if(isLoggedIn):
        has_unread_notifications = Notification.objects.filter(
            email=request.session["email"],
            is_read=False
        ).exists()

    vehicles = Vehicle.objects.filter(status__iexact="available")
    return render(request, "home.html", {"has_unread_notifications":has_unread_notifications,"vehicles": vehicles,"logged_in":isLoggedIn,"is_driver":isDriver})

def user_notifications(request):
    email = request.session.get("email")
    if not email:
        return redirect("login")

    notifications = Notification.objects.filter(email=email).order_by('-created_at')
    notifications.update(is_read=True)
    notifications = Notification.objects.filter(email=email).order_by('-created_at')
    return render(request, "notifications.html", {
        "notifications": notifications
    })

@csrf_exempt
def queue_booking(request, vehicle_id):
    isLoggedIn = request.session.get("logged_in", False)
    if not isLoggedIn:
        return redirect("login")

    email = request.session.get("email")
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    # Check if vehicle is already booked/queued by this user
    already_in_cart = VehicleBooking.objects.filter(
        email=email, vehicle_number=vehicle.vehicle_number
    ).exists()

    if request.method == "POST" and not already_in_cart:
        booking_date = request.POST.get("booking_date")
        booking_time = request.POST.get("booking_time")
        num_days = request.POST.get("num_days")
        driver_needed = request.POST.get("driver_needed")

        if not all([booking_date, booking_time, num_days, driver_needed, email]):
            messages.error(request, "All fields are required and you must be logged in!")
            return redirect('queue_booking', vehicle_id=vehicle.id)

        try:
            num_days = int(num_days)
        except ValueError:
            messages.error(request, "Number of days must be a number.")
            return redirect('queue_booking', vehicle_id=vehicle.id)

        VehicleBooking.objects.create(
            brand=vehicle.brand,
            vehicle_name=vehicle.vehicle_name,
            vehicle_type=vehicle.vehicle_type,
            rent_price=vehicle.rent_price,
            vehicle_number=vehicle.vehicle_number,
            booking_date=booking_date,
            booking_time=booking_time,
            num_days=num_days,
            driver_needed=driver_needed,
            email=email
        )

        if(driver_needed):
            print("driver needed")
            print(vehicle.vehicle_name)
            DriverRequests.objects.create(
                requester_email = email,
                vehicle_name = vehicle.vehicle_name,
                vehicle_type = vehicle.vehicle_type,
            )
        

        messages.success(request, "Your booking has been queued successfully!")
        return redirect('queue_booking', vehicle_id=vehicle.id)

    return render(request, "queue_booking.html", {
        'vehicle': vehicle,
        'logged_in': isLoggedIn,
        'already_in_cart': already_in_cart
    })
def my_bookings(request):
    email = request.session.get("email")
    if not email:
        return redirect('login')

    if request.method == "POST":
        action = request.POST.get("action")
        booking_id = request.POST.get("booking_id")
        
        if action == "cancel" and booking_id:
            booking = get_object_or_404(VehicleBooking, id=booking_id, email=email)

            if booking.status in ["pending", "accepted"]:
                # Optional: free vehicle if already accepted
                if booking.status == "accepted":
                    try:
                        vehicle = Vehicle.objects.get(vehicle_number=booking.vehicle_number)
                        vehicle.status = "Available"
                        vehicle.save()
                    except Vehicle.DoesNotExist:
                        pass
                Bids.objects.filter(
                    vehicle_name=booking.vehicle_name,
                    requester_email=booking.email
                ).delete()

                # ----------------- DELETE DRIVER REQUEST -----------------
                DriverRequests.objects.filter(
                    vehicle_name=booking.vehicle_name,
                    requester_email=booking.email
                ).delete()

                # ----------------- DELETE BOOKING -----------------
                booking.delete()
                messages.success(request, "Booking cancelled successfully.")

            else:
                messages.error(request, "Cannot cancel this booking.")
        if action == "confirm" and booking_id:
            booking = get_object_or_404(VehicleBooking, id=booking_id, email=email)

            # Get lowest bid + bidder
            lowest_bid_obj = Bids.objects.filter(
                vehicle_name=booking.vehicle_name,
                requester_email=booking.email
            ).order_by('bid_amount').first()

            if lowest_bid_obj:
                # Update Driver Request
                DriverRequests.objects.filter(
                    vehicle_name=booking.vehicle_name,
                    requester_email=booking.email
                ).update(
                    user_accepted=True,
                    lowest_bid=lowest_bid_obj.bid_amount,
                    lowest_bidder_email=lowest_bid_obj.bidder
                )

                messages.success(request, "Driver accepted successfully.")
            else:
                messages.error(request, "No bids available to confirm.")

            return redirect("my_bookings")
        return redirect("my_bookings")

    bookings = VehicleBooking.objects.filter(email=email).order_by('-id')

    # Attach vehicle image and total price
    for booking in bookings:
        try:
            vehicle = Vehicle.objects.get(vehicle_number=booking.vehicle_number)
            booking.vehicle_image = vehicle.vehicle_image.url
        except Vehicle.DoesNotExist:
            booking.vehicle_image = None

    for booking in bookings:
    # ----- BIDS -----
        lowest = Bids.objects.filter(
            vehicle_name=booking.vehicle_name,
            requester_email=booking.email
        ).order_by('bid_amount').values_list('bid_amount', flat=True).first()

        booking.has_bid = lowest is not None
        booking.lowest_bid = lowest

        # ----- DRIVER REQUEST (USER ACCEPTED FLAG) -----
        driver_req = DriverRequests.objects.filter(
            vehicle_name=booking.vehicle_name,
            requester_email=booking.email
        ).first()

        if driver_req:
            booking.user_accepted = driver_req.user_accepted
        else:
            booking.user_accepted = False
    return render(request, "my_bookings.html", {"bookings": bookings})


def driver_requests(request):
    # ----------------- Session check -----------------
    isDriver = request.session.get("is_driver")
    if not isDriver:
        return redirect('login')

    email = request.session.get("email")
    driver = get_object_or_404(Driver, email=email)

    # ----------------- Allowed vehicle types -----------------
    try:
        allowed_types = json.loads(driver.vehicle_types)
    except:
        allowed_types = []

    # ----------------- Handle bid -----------------
    if request.method == "POST":
        request_id = request.POST.get("request_id")
        bid_amount = request.POST.get("bid_amount")

        driver_request = get_object_or_404(DriverRequests, id=request_id)

        try:
            bid_amount = int(bid_amount)
        except:
            bid_amount = 0

        if bid_amount > 0:
            # Save bid
            Bids.objects.create(
                vehicle_name=driver_request.vehicle_name,
                requester_email=driver_request.requester_email,
                bidder=email,
                bid_amount=bid_amount
            )

            # Update lowest bid
            if driver_request.lowest_bid == 0 or bid_amount < driver_request.lowest_bid:
                driver_request.lowest_bid = bid_amount
                driver_request.lowest_bidder_email = email
                driver_request.save()

    # ----------------- Get requests -----------------
    requests = DriverRequests.objects.filter(
        vehicle_type__in=allowed_types
    ).order_by('-id')

    for r in requests:
    # Get vehicle safely
        vehicle = Vehicle.objects.filter(vehicle_name=r.vehicle_name).first()

        if vehicle:
            if vehicle.vehicle_image:
                r.vehicle_image = vehicle.vehicle_image.url
            else:
                r.vehicle_image = None

            r.brand = vehicle.brand
            r.rent_price = vehicle.rent_price
            r.fuel_type = vehicle.fuel_type
        else:
            r.vehicle_image = None
            r.brand = ""
            r.rent_price = 0
            r.fuel_type = "" \
        # ----------------- Get booking details -----------------
        booking = VehicleBooking.objects.filter(
            vehicle_name=r.vehicle_name,
            # optional: match same requester for accuracy
            # requester_email=r.requester_email
        ).order_by('-id').first()

        if booking:
            r.booking_date = booking.booking_date
            r.booking_time = booking.booking_time
            r.num_days = booking.num_days
        else:
            r.booking_date = None
            r.booking_time = None
            r.num_days = None

        # ----------------- Bid logic -----------------
        user_bid = Bids.objects.filter(
            vehicle_name=r.vehicle_name,
            requester_email=r.requester_email,
            bidder=email
        ).first()

        if not user_bid:
            r.bid_status = "pending"
        elif r.lowest_bidder_email == email:
            r.bid_status = "winning"
        else:
            r.bid_status = "outbid"

    return render(request, "driver_requests.html", {
        "requests": requests,
        "driver": driver
    })

@csrf_exempt
def login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data["email"]
        password = data["password"]
        try:
            u = Users.objects.get(email = email)

            if(password == u.password):
                request.session["logged_in"] = True
                request.session["email"] = email
                try:
                    d = Driver.objects.get(email=email)
                    print("is_driver")
                    request.session["is_driver"] = True
                except Driver.DoesNotExist:
                    request.session["is_driver"] = False
                return JsonResponse({
                    "login_state":"login_success",
                }) 
            else:
                return JsonResponse({
                    "login_state":"password_wrong",
                }) 
        except Users.DoesNotExist:
            return JsonResponse({
                "login_state":"email_wrong",
            }) 

    return render(request,"login.html")
@csrf_exempt
def signup(request):
    if request.method == "POST":
        req = json.loads(request.body)
        if(req["action"]=="create_acc"):
            try:
                u = Users(
                    firstName = req["firstName"],
                    lastName = req["lastName"],
                    email = req["email"],
                    password = req["passwd"]
                )

                u.save()
                print(u)
                return JsonResponse({
                    "account_created":True,
                })
            except Exception as e:
                return JsonResponse({
                    "account_created":False,
                }) 
    return render(request,"sign_up.html")
@csrf_exempt
def admin_login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user = Users.objects.get(email=data['email'])
        if(user.privilage == "admin"):
            request.session["logged_in"] = True
            request.session["email"] = data['email']
            request.session["privilage"] = "admin"
            return JsonResponse({
                "admin_verified":True,
            }) 
        elif user.privilage != "admin":
            return JsonResponse({
                "admin_verified":False,
            })
    return render(request,"admin.html")

@csrf_exempt
def admin_dashboard(request):
    try:
        if request.session["privilage"] == "admin":
            return render(request,"admin_dashboard.html")
        else:
            return render(request,"no_access.html")
    except:
        return render(request,"no_access.html")
@csrf_exempt
def add_driver(request):
    if request.method == "POST":
        try:
            Driver.objects.create(
                name=request.POST.get("name"),
                license_number=request.POST.get("license"),
                phone=request.POST.get("phone"),
                email=request.POST.get("email"),
                status=request.POST.get("status"),
                photo=request.FILES.get("photo"),
                vehicle_types=request.POST.get("vehicle_types")  # JSON string
            )

            return JsonResponse({"status": "success"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return render(request, "add_driver.html")

@csrf_exempt
def manage_drivers(request):
    drivers = Driver.objects.all()
    return render(request,"manage_drivers.html",{
        "drivers":drivers
    })

@csrf_exempt
def edit_driver(request):
    return render(request,"edit_driver.html")

@csrf_exempt
def add_vehicle(request):

    if request.method == "POST":
        try:
            vehicle_name = request.POST.get("vehicle_name")
            vehicle_number = request.POST.get("vehicle_number")
            brand = request.POST.get("brand")
            rent_price = request.POST.get("rent_price")
            fuel_type = request.POST.get("fuel_type")
            status = request.POST.get("status")
            vehicle_type = request.POST.get("vehicle_type")  
            vehicle_image = request.FILES.get("vehicle_image")

            Vehicle.objects.create(
                vehicle_name=vehicle_name,
                vehicle_number=vehicle_number,
                brand=brand,
                rent_price=rent_price,
                fuel_type=fuel_type,
                status=status,
                vehicle_type=vehicle_type, 
                vehicle_image=vehicle_image
            )

            return redirect("/manage_vehicle/")

        except Exception as e:
            return JsonResponse({"status":"error","message":str(e)})

    return render(request,"add_vehicle.html")

@csrf_exempt
def manage_vehicle(request):
    vehicles = Vehicle.objects.all()
    return render(request, "manage_vehicle.html", {"vehicles": vehicles})

@csrf_exempt
def edit_vehicle(request, id):
    vehicle = Vehicle.objects.get(id=id)

    return render(request, "edit_vehicle.html", {
        "vehicle": vehicle
    })

@csrf_exempt
def delete_vehicle(request, id):
    if request.method == "POST":
        vehicle = get_object_or_404(Vehicle, id=id)
        Bids.objects.filter(
            vehicle_name=vehicle.vehicle_name,
        ).delete()
        DriverRequests.objects.filter(
            vehicle_name=vehicle.vehicle_name,
        ).delete()
        vehicle.delete()
        return redirect("/manage_vehicle/")
    return render(request,"manage_vehicle.html")


@csrf_exempt
def update_vehicle(request):

    if request.method == "POST":

        vehicle_id = request.POST.get("id")
        vehicle = Vehicle.objects.get(id=vehicle_id)

        old_status = vehicle.status

        vehicle.vehicle_name = request.POST.get("vehicle_name")
        vehicle.vehicle_number = request.POST.get("vehicle_number")
        vehicle.brand = request.POST.get("brand")
        vehicle.rent_price = request.POST.get("rent_price")
        vehicle.fuel_type = request.POST.get("fuel_type")
        vehicle.status = request.POST.get("status")
        vehicle.vehicle_type = request.POST.get("vehicle_type")

        # update image only if new uploaded
        if request.FILES.get("vehicle_image"):
            vehicle.vehicle_image = request.FILES.get("vehicle_image")

        vehicle.save()
         # If vehicle changed from Rented → Available
        if old_status == "Rented" and vehicle.status == "Available":

            # get latest booking for this vehicle (no status filter)
            booking = VehicleBooking.objects.filter(
                vehicle_number=vehicle.vehicle_number
            ).order_by('-id').first()
            print(booking)
            if booking:
                booking.delete()
        return redirect("/manage_vehicle/")
    return redirect("/manage_vehicle/")

@csrf_exempt
def manage_rental_status(request):
    bookings = VehicleBooking.objects.all().order_by('-booking_date')

    for b in bookings:
        # Get lowest bid for this booking
        lowest_bid = Bids.objects.filter(
            vehicle_name=b.vehicle_name,
            requester_email=b.email
        ).order_by('bid_amount').first()

        if lowest_bid:
            print("l: ",lowest_bid)
            b.lowest_bid = lowest_bid.bid_amount
            b.lowest_bidder = lowest_bid.bidder
        else:
            b.lowest_bid = None
            b.lowest_bidder = None
        # ----- USER ACCEPTED FLAG -----
        driver_req = DriverRequests.objects.filter(
            vehicle_name=b.vehicle_name,
            requester_email=b.email
        ).first()

        if driver_req:
            b.user_accepted = driver_req.user_accepted
        else:
            b.user_accepted = False


    return render(request, "manage_rental_status.html", {'bookings': bookings})

@csrf_exempt
def accept_booking(request, booking_id):
    booking = get_object_or_404(VehicleBooking, id=booking_id)

    if booking.status == "pending":

        driver = None

        # ---------------- DRIVER ASSIGN ----------------
        if booking.driver_needed == "yes":
            lowest_bid = Bids.objects.filter(
                vehicle_name=booking.vehicle_name,
                requester_email=booking.email
            ).order_by('bid_amount').first()

            if not lowest_bid:
                messages.error(request, "Cannot accept. No drivers have bid yet.")
                return redirect('manage_rental_status')

            driver = Driver.objects.filter(email=lowest_bid.bidder).first()

            if not driver:
                messages.error(request, "Driver not found.")
                return redirect('manage_rental_status')

            booking.driver_email = driver.email  # make sure field exists

        # ---------------- UPDATE BOOKING ----------------
        booking.status = "accepted"
        booking.save()

        # ---------------- UPDATE VEHICLE ----------------
        try:
            vehicle = Vehicle.objects.get(vehicle_number=booking.vehicle_number)
            vehicle.status = "Rented"
            vehicle.save()
        except Vehicle.DoesNotExist:
            traceback.print_exc()

        # ---------------- USER DETAILS ----------------
        user = Users.objects.filter(email=booking.email).first()
        user_phone = getattr(user, "phone", "N/A")

        # ---------------- NOTIFY USER ----------------
        if not driver:
            Notification.objects.create(
                email=booking.email,
                message=f"""
                    Booking Confirmed!
                    Feel free to pickup the vehicle on assigned day, Please coordinate for pickup.
                """
            )

        # ---------------- NOTIFY DRIVER ----------------
        if driver:

            Notification.objects.create(
            email=booking.email,
            message=f"""
                Booking Confirmed!

                Vehicle: {booking.vehicle_name}
                Date: {booking.booking_date}
                Time: {booking.booking_time}
                Days: {booking.num_days}

                Driver Details:
                Name: {driver.name if driver else 'Not Required'}
                Phone: {driver.phone if driver else 'N/A'}
                License: {driver.license_number if driver else 'N/A'}

                Please coordinate for pickup.
            """
        )

            Notification.objects.create(
                email=driver.email,
                message=f"""
                    New Ride Assigned!

                    Customer Email: {booking.email}
                    Customer Phone: {user_phone}

                    Vehicle: {booking.vehicle_name}
                    Date: {booking.booking_date}
                    Time: {booking.booking_time}
                    Days: {booking.num_days}

                    Contact customer and proceed.
                """
            )
        # ---------------- NOTIFY OUTBID DRIVERS ----------------
            all_bids = Bids.objects.filter(
                vehicle_name=booking.vehicle_name,
                requester_email=booking.email
            )

            for bid in all_bids:
                # skip winning driver
                if driver and bid.bidder == driver.email:
                    continue

                outbid_driver = Driver.objects.filter(email=bid.bidder).first()

                if outbid_driver:
                    Notification.objects.create(
                        email=outbid_driver.email,
                        message=f"""
            Unfortunately, you have been outbid.<br><br>

            Vehicle: {booking.vehicle_name}
            Date: {booking.booking_date}
            Time: {booking.booking_time}

            Another driver has been selected for this request.<br>
            You can explore and bid on other available requests.
            """
                    )

        # ---------------- CLEANUP ----------------
        Bids.objects.filter(
            vehicle_name=booking.vehicle_name,
            requester_email=booking.email
        ).delete()

        DriverRequests.objects.filter(
            vehicle_name=booking.vehicle_name,
            requester_email=booking.email
        ).delete()

        


        messages.success(
            request,
            "Booking accepted, driver assigned, and notifications sent."
        )

    return redirect('manage_rental_status')

@csrf_exempt
def edit_rental_status(request):
    return render(request,"edit_rental_status.html")
@csrf_exempt
def logout_view(request):
    request.session.flush()   # removes all session data
    print(request.session)
    return redirect("home")      # re
@csrf_exempt
def delete_driver(request):

    if request.method == "POST":
        driver_id = request.POST.get("id")
        Driver.objects.filter(id=driver_id).delete()

    return redirect("/manage_drivers/")

def reject_booking(request, booking_id):
    booking = get_object_or_404(VehicleBooking, id=booking_id)

    if booking.status == "pending":
        try:
            # ---------------- GET ALL DRIVERS WHO BID ----------------
            bids = Bids.objects.filter(
                vehicle_name=booking.vehicle_name,
                requester_email=booking.email
            )

            # ---------------- NOTIFY USER ----------------
            Notification.objects.create(
                email=booking.email,
                message=f"""
                    Booking Rejected

                    Vehicle: {booking.vehicle_name}
                    Date: {booking.booking_date}
                    Time: {booking.booking_time}
                    Days: {booking.num_days}

                    Unfortunately, your booking has been rejected.
                    Please try another vehicle.
                """
            )

            # ---------------- NOTIFY DRIVERS ----------------
            for bid in bids:
                driver = Driver.objects.filter(email=bid.bidder).first()

                if driver:
                    Notification.objects.create(
                        email=driver.email,
                        message=f"""
                        Request Cancelled

                        Vehicle: {booking.vehicle_name}
                        Date: {booking.booking_date}
                        Time: {booking.booking_time}
                        Days: {booking.num_days}

                        The customer has cancelled or the request was rejected.
                        You can bid on other requests.
                        """
                    )

            # ---------------- CLEANUP ----------------
            bids.delete()

            DriverRequests.objects.filter(
                vehicle_name=booking.vehicle_name,
                requester_email=booking.email
            ).delete()

            # ---------------- DELETE BOOKING ----------------
            booking.delete()

            messages.error(request, "Booking rejected, all drivers notified.")

        except Exception:
            traceback.print_exc()
            messages.error(request, "Error while rejecting booking.")

    return redirect('manage_rental_status')

@csrf_exempt
def manage_drivers_edit(request, id):

    driver = Driver.objects.get(id=id)

    return render(request,"manage_drivers_edit.html",{
        "driver":driver
    })

@csrf_exempt
def update_driver(request):
    if request.method == "POST":

        driver_id = request.POST.get("id")
        driver = Driver.objects.get(id=driver_id)

        driver.name = request.POST.get("name")
        driver.license_number = request.POST.get("license")
        driver.phone = request.POST.get("phone")
        driver.email = request.POST.get("email")
        driver.status = request.POST.get("status")

        driver.vehicle_types = request.POST.get("vehicle_types")

        if request.FILES.get("photo"):
            driver.photo = request.FILES.get("photo")

        driver.save()

    return redirect("/manage_drivers/")