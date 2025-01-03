from rest_framework.response import Response
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny

from django.shortcuts import redirect
from django.db import models
from django.db.models.functions import ExtractMonth
from django.core.files.uploadedfile import InMemoryUploadedFile


from api import models as api_models
from api import serializers as api_serializers

from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings

from distutils.util import strtobool
import stripe
import stripe.error
import requests


stripe.api_key = settings.STRIPE_SECRET_KEY
PAYPAL_SECRET_ID = settings.PAYPAL_SECRET_ID
PAYPAL_CLIENT_ID = settings.PAYPAL_CLIENT_ID

class CategoryListAPIView(generics.ListAPIView):
    queryset = api_models.Category.objects.filter(active=True)
    serializer_class = api_serializers.CategorySerializer
    permission_classes = [AllowAny]



class CourseListAPIView(generics.ListAPIView):
    queryset = api_models.Course.objects.filter(platform_status="Published", teacher_course_status="Published")
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

@api_view
def your_view(request):
    data = request.data  # or your method of obtaining request data
    print(data)  # To verify the incoming data
    serializer = api_serializers.VariantSerializer(data=data)
    if serializer.is_valid():
        # Do something
        pass
    else:
        print(serializer.errors)




class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        slug = self.kwargs['slug']
        course = api_models.Course.objects.get(slug=slug, platform_status="Published", teacher_course_status="Published")
        return course
    
    

class CartAPIView(generics.CreateAPIView):
    queryset = api_models.Cart.objects.all()
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        course_id = request.data['course_id']
        user_id = request.data['user_id']
        price = request.data['price']
        country_name = request.data['country_name']
        cart_id = request.data['cart_id']

        course = api_models.Course.objects.filter(id=course_id).first()

        if user_id != "undefined":
            user = api_models.User.objects.filter(id=user_id).first()
        else:
            user = None

        try:
            country_object = api_models.Country.objects.filter(name=country_name).first()
            country = country_object.name
        except:
            country_object = None
            country = "Kenya"

        if country_object:
            tax_rate = country_object.tax_rate / 100
        else:
            tax_rate = 5 / 100

        cart = api_models.Cart.objects.filter(course=course).first()

        if cart:
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.Total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.country = country
            cart.cart_id = cart_id

            cart.save()

            return Response({"Message": "Cart Updated Successfully"}, status=status.HTTP_200_OK)
        else: 
            cart = api_models.Cart()
    
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.Total = Decimal(cart.price) + Decimal(cart.tax_fee)
            cart.country = country
            cart.cart_id = cart_id

            cart.save()

            return Response({"Message": "Cart Created Successfully"}, status=status.HTTP_201_CREATED)
        



class CartListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]
    queryset = api_models.Cart.objects.all()




class CartItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        cart_id = self.kwargs['cart_id']
        item_id = self.kwargs['item_id']
        delete = api_models.Cart.objects.filter(cart_id=cart_id, id=item_id).first()
        print(f"deleted******* {delete}")
        return delete
        # return Response(status=status.HTTP_204_NO_CONTENT)


class CartStatsAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]
    lookup_field = 'user_id'

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        queryset = api_models.Cart.objects.filter(user=user_id)
        return queryset
    
    def get(self, request, *args, **kwargs):
        query = self.get_queryset()

        total_price = 0.00
        total_tax = 0.00
        total_total = 0.00

        for cart_item in query:
            total_price += float(cart_item.price)
            total_tax += float(cart_item.tax_fee)
            total_total += round(float(cart_item.Total), 2)

        print(total_price, total_tax, total_total)

        data = {
            "total_price": total_price,
            "tax_fee": total_tax,
            "total_amount": total_total
        }

        return Response(data, status=status.HTTP_200_OK)


class CreateOrderAPIView(generics.CreateAPIView):
    queryset = api_models.CartOrder.objects.all()
    serializer_class = api_serializers.CartOrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        full_name = request.data['full_name']
        email = request.data['email']
        country = request.data['country']
        cart_id = request.data['cart_id']
        user_id = request.data['user_id']

        if user_id != 0:
            user = api_models.User.objects.get(id=user_id)
        else:
            user = None

        cart = api_models.Cart.objects.filter(user=user_id, cart_id=cart_id)

        total_price = Decimal(0.00)
        total_tax = Decimal(0.00)
        total_total = Decimal(0.00)
        total_initial_total = Decimal(0.00)

        order = api_models.CartOrder.objects.create(
            full_name=full_name,
            email=email,
            country=country,
            student=user
        )

        for item in cart:
            api_models.CartOrderItem.objects.create(
                order=order,
                course=item.course,
                price=item.price,
                tax_fee=item.tax_fee,
                total=item.Total,
                initial_total=item.Total,
                teacher=item.course.teacher
            )

            total_price += Decimal(item.price)
            total_tax += Decimal(item.tax_fee)
            total_initial_total += Decimal(item.Total)
            total_total += Decimal(item.Total)

            order.teacher.add(item.course.teacher)

        order.sub_total = total_price
        order.tax_fee = total_tax
        order.total = total_total
        order.initial_total = total_initial_total
        order.save()


        return Response({"message": "Order created successfuly!", "order_oid": order.oid}, status=status.HTTP_201_CREATED)


class CheckOutAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = api_models.CartOrder.objects.all()
    lookup_field ='oid'


class CouponApplyAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CouponSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        order_oid = request.data['order_oid']
        coupen_code = request.data['coupon_code']

        order = api_models.CartOrder.objects.get(oid=order_oid)
        coupon = api_models.Coupon.objects.get(code=coupen_code)

        if coupon:
            order_items = api_models.CartOrderItem.objects.filter(order=order, teacher=coupon.teacher)
            for i in order_items:
                if not coupon in i.coupons.all():
                    discount = i.total * coupon.discount / 100

                    i.total -= discount
                    i.price -= discount
                    i.saved += discount
                    i.applied_coupon = True
                    i.coupons.add(coupon)

                    order.coupons.add(coupon)
                    order.total -= discount
                    order.sub_total -= discount
                    order.saved += discount

                    i.save()
                    order.save()
                    coupon.used_by.add(order.student)
                    return Response({"Message": "Coupon Found and Activated", "icon": "success"}, status=status.HTTP_201_CREATED)
                else:
                    return Response({"Message": "Coupon Already Applied", "icon": "warning"}, status=status.HTTP_200_OK)
        else:
            return Response({"Message": "Coupon Not Found", "icon": "error"}, status=status.HTTP_404_NOT_FOUND)


class StripeCheckOutAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        
        order_oid = self.kwargs['order_oid']
        order = api_models.CartOrder.objects.get(oid=order_oid)

        if not order:
            return Response({"Message": "Order Not Found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=order.email,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': order.full_name
                            },
                            'unit_amount': int(order.total)
                        },
                        'quantity': 1
                    }
                ],
                mode='payment',
                success_url=settings.FRONTEND_SITE_URL + "payment-success/" + order.oid + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.FRONTEND_SITE_URL + "payment-failed/"
            )

            print("checkout_session ********:", checkout_session)

            order.stripe_session_id = checkout_session.id
            order.save()
            return redirect(checkout_session.url)
        except stripe.error.StripeError as e:
            return Response({"Message": f"Something went wrong when trying to make payment. Error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        

def get_access_token(client_id, secret_key):
    token_url = "https://api.sanbox.paypal.com/v1/oauth/token"
    data = {'grant_type': 'client_credentials'}
    auth = (client_id, secret_key)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        print("Access Token ->", response.json()['access_token'])
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to get access token from paypal {response.status_code}")
    

class PaymentSuccessAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    permission_classes = [AllowAny]
    queryset = api_models.CartOrder.objects.all()

    def create(self, request, *args, **kwargs):
        order_oid = request.data['order_oid']
        session_id = request.data['session_id']
        paypal_order_id = request.data['paypal_order_id']

        order = api_models.CartOrder.objects.get(oid=order_oid)
        order_items = api_models.CartOrderItem.objects.filter(order=order)

        # paypal payment success
        if paypal_order_id != "null":
            paypal_api_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {get_access_token(PAYPAL_CLIENT_ID, PAYPAL_SECRET_ID)}'
            }
            response = requests.get(paypal_api_url, headers=headers)

            if response.status_code == 200:
                paypal_order_data = response.json()
                paypal_payment_status = paypal_order_data['status']

                if paypal_payment_status == "COMPLETED":
                    if order.payment_status == "Processing":
                        order.payment_status = "Paid"
                        order.save()

                        # notifications
                        api_models.Notification.objects.create(
                            user=order.student,
                            order=order,
                            type="Course Enrollment Completed"
                        )

                        for i in order_items:
                            api_models.Notification.objects.create(
                                teacher=i.teacher,
                                order=order,
                                order_item=i,
                                type="New Order"
                            )

                            api_models.EnrolledCourse.objects.create(
                                course=i.course,
                                user=order.student,
                                teacher=i.teacher,
                                order_item=i
                            )
                        return Response({"Message": "Payment Successfull"}, status=status.HTTP_200_OK)
                    else:
                        return Response({"Message": "You have already paid."}, status=status.HTTP_200_OK)
                else:
                    return Response({"Message": "Payment Failed! Please try again!"}, status=status.HTTP_404_NOT_FOUND)
                
            else: 
                return Response({"Message": "Paypal Error occured"}, status=status.HTTP_400_BAD_REQUEST)

        # stripe payment success
        if session_id != "null":
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                if order.payment_status == "Processing":
                        order.payment_status = "Paid"
                        order.save()

                        # notifications
                        api_models.Notification.objects.create(
                            user=order.student,
                            order=order,
                            type="Course Enrollment Completed"
                        )

                        for i in order_items:
                            api_models.Notification.objects.create(
                                teacher=i.teacher,
                                order=order,
                                order_item=i,
                                type="New Order"
                            )

                            api_models.EnrolledCourse.objects.create(
                                course=i.course,
                                user=order.student,
                                teacher=i.teacher,
                                order_item=i
                            )


                        return Response({"Message": "Payment Successfull"}, status=status.HTTP_200_OK)
                else:
                    return Response({"Message": "You have already paid."}, status=status.HTTP_200_OK)
            else:
                return Response({"Message": "Payment Failed! Please try again!"}, status=status.HTTP_404_NOT_FOUND)

class SearchCourseAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.GET.get('query')
        return api_models.Course.objects.filter(title__icontains=query, platform_status="Published", teacher_course_status="Published")
    
    
class StudentSummaryAPIView(generics.ListAPIView):
    serializer_class = api_serializers.StudentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = api_models.User.objects.get(id=user_id)

        total_courses = api_models.EnrolledCourse.objects.filter(user=user).count()
        completed_lesons = api_models.Completedlesson.objects.filter(user=user).count()
        achieved_certificates = api_models.Certificate.objects.filter(user=user).count()

        return [{
            'total_courses': total_courses,
            'completed_lesons': completed_lesons,
            'achieved_certificates': achieved_certificates
        }]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

class StudentCourseListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.EnrolledCourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = api_models.User.objects.get(id=user_id)
        return api_models.EnrolledCourse.objects.filter(user=user)
    
class StudentCourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.EnrolledCourseSerializer
    permission_classes = [AllowAny]
    lookup_field = 'enrollemnt_id'

    def get_object(self):
        user_id = self.kwargs['user_id']
        enrollment_id = self.kwargs['enrollment_id']

        user = api_models.User.objects.get(id=user_id)
        enrollment = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id, user=user)
        return enrollment
    
class StudentCourseCompletedCreateAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CompletedLessonSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        course_id = request.data['course_id']
        variant_item_id = request.data['variant_item_id']

        user = api_models.User.objects.get(id=user_id)
        course = api_models.Course.objects.get(id=course_id)
        variantItem = api_models.VariantItem.objects.get(variant_item_id=variant_item_id)

        completed_lessons = api_models.Completedlesson.objects.filter(user=user, course=course, variant_item=variantItem).first()

        if completed_lessons:
            completed_lessons.delete()
            return Response({"Message": "Course marked as not completed"})
        else:
            api_models.Completedlesson.objects.create(user=user, course=course, variant_item=variantItem)
            return Response({"Message": "Course marked as completed"})
        
class StudentCreateNoteAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializers.NotesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        enrollment_id = self.kwargs['enrollment_id']

        user = api_models.User.objects.get(id=user_id)
        enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)

        return api_models.Notes.objects.filter(user=user, course=enrolled.course)

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        enrollment_id = request.data['enrollment_id']
        title = request.data['title']
        note = request.data['note']

        user = api_models.User.objects.get(id=user_id)
        enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)

        api_models.Notes.objects.create(
            user=user,
            course=enrolled.course,
            note=note,
            title=title
        )

        return Response({'Message': "Note creates successfully"}, status=status.HTTP_201_CREATED)

    
    
class StudentNoteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializers.NotesSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        enrollment_id = self.kwargs['enrollment_id']
        note_id = self.kwargs['note_id']

        user = api_models.User.objects.get(id=user_id)
        enrolled = api_models.EnrolledCourse.objects.get(enrollment_id=enrollment_id)
        note = api_models.Notes.objects.get(user=user, course=enrolled.course, id=note_id)
        return note
    
class StudentRateCourseCreateAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        course_id = request.data['course_id']
        rating = request.data['rating']
        review = request.data['review']

        user = api_models.User.objects.get(id=user_id)
        course = api_models.Course.objects.get(id=course_id)


        api_models.Review.objects.create(
            user=user,
            course=course,
            review=review,
            rating=rating
        )

        return Response({'Messages': 'Review Created successfully'}, status=status.HTTP_201_CREATED)

class StudentRateCourseUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        review_id = self.kwargs['review_id']

        user = api_models.User.objects.get(id=user_id)
        return api_models.Review.objects.get(id=review_id, user=user)
    
class StudentWishListListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializers.WishListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = api_models.User.objects.get(id=user_id)
        return api_models.WishList.objects.filter(user=user)
    
    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        course_id = request.data['course_id']

        user = api_models.User.objects.get(id=user_id)
        course = api_models.Course.objects.get(id=course_id)
        wishlist = api_models.WishList.objects.filter(user=user, course=course).first()

        if wishlist:
            wishlist.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            api_models.WishList.objects.create(
                user=user,
                course=course
            )
            return Response({"Message": "Wishiist Created"}, status=status.HTTP_201_CREATED)
        
class QuestionAnswerListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializers.QuestionAnswerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        course = api_models.Course.objects.get(id=course_id)
        return api_models.Question_Answer.objects.filter(course=course)
    
    def create(self, request, *args, **kwargs):
        course_id = request.data['course_id']
        user_id = request.data['user_id']
        title = request.data['title']
        message = request.data['message']

        user = api_models.User.objects.get(id=user_id)
        course = api_models.Course.objects.get(id=course_id)
        question = api_models.Question_Answer.objects.create(
            course=course,
            user=user,
            title=title
        )

        api_models.Question_Answer_Message.objects.create(
            course=course,
            user=user,
            message=message,
            question=question
        )

        return Response({"Message": "Group conversation started"}, status=status.HTTP_201_CREATED)
    
class QuestionAnswerMessageSendAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.QuestionAnswerMessageSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        course_id = request.data['course_id']
        user_id = request.data['user_id']
        qa_id = request.data['qa_id']
        message = request.data['message']

        user = api_models.User.objects.get(id=user_id)
        course = api_models.Course.objects.get(id=course_id)
        question = api_models.Question_Answer.objects.get(qa_id=qa_id)

        api_models.Question_Answer_Message.objects.create(
            course=course,
            user=user,
            message=message,
            question=question
        )

        question_serializer = api_serializers.QuestionAnswerSerializer(question)

        return Response({'Message': 'Message send', 'Question': question_serializer.data}, status=status.HTTP_201_CREATED)
    
class TeacherSummaryAPIView(generics.ListAPIView):
    serializer_class = api_serializers.TeacherSummarySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)

        one_month_ago = datetime.today() - timedelta(days=28)

        total_courses = api_models.Course.objects.filter(teacher=teacher).count()
        total_revenue = api_models.CartOrderItem.objects.filter(teacher=teacher, order__payment_status='Paid').aggregate(total_revenue=models.Sum("price"))['total_revenue'] or 0
        monthly_revenue = api_models.CartOrderItem.objects.filter(teacher=teacher, order__payment_status='Paid', date__gte=one_month_ago).aggregate(total_revenue=models.Sum("price"))['total_revenue'] or 0


        enrolled_courses = api_models.EnrolledCourse.objects.filter(teacher=teacher)
        unique_student_ids = set()
        all_students = []

        for course in enrolled_courses:
            if course.user_id not in unique_student_ids:
                userProfile = api_models.Profile.objects.filter(user=course.user_id).first()
                students = {
                    "full_name": userProfile.full_name,
                    "image": userProfile.image.url,
                    "country": userProfile.country,
                    "date": course.date
                }

                all_students.append(students)
                unique_student_ids.add(course.user)
        
        return [{
            "total_courses": total_courses,
            "total_revenue": total_revenue,
            "monthly_revenue": monthly_revenue,
            "total_students": len(all_students)
        }]
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class TeacherCourseListView(generics.ListAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Course.objects.filter(teacher=teacher)
    
class TeacherReviewListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Review.objects.filter(course__teacher=teacher)
    
class TeacherReviewDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        review_id = self.kwargs['review_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Review.objects.filter(course__teacher=teacher, id=review_id).first()
    
class TeacherStudentListAPIView(viewsets.ViewSet):
    def list(self, request, teacher_id=None):
        teacher = api_models.Teacher.objects.get(id=teacher_id)

        enrolled_courses = api_models.EnrolledCourse.objects.filter(teacher=teacher)
        unique_student_ids = set()
        all_students = []

        for course in enrolled_courses:
            if course.user_id not in unique_student_ids:
                userProfile = api_models.Profile.objects.filter(user=course.user_id).first()
                students = {
                    "full_name": userProfile.full_name,
                    "image": userProfile.image.url,
                    "country": userProfile.country,
                    "date": course.date
                }

                all_students.append(students)
                unique_student_ids.add(course.user)

        return Response(all_students, status=status.HTTP_200_OK)
    
@api_view(('GET', ))
def TeacherALlMonthEarningAPIView(request, teacher_id):
    teacher = api_models.Teacher.objects.get(id=teacher_id)
    monthly_earning_tracker = (
        api_models.CartOrderItem.objects
        .filter(teacher=teacher, order__payment_status="Paid")
        .annotate(month=ExtractMonth('date'))
        .values("month")
        .annotate(
            total_earning=models.Sum('price')
        )
        .order_by('month')
    )

    return Response(monthly_earning_tracker)

class TeacherBestSellingCourseAPIView(viewsets.ViewSet):

    def list(self, request, teacher_id=None):
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        courses_with_total_price = []
        courses = api_models.Course.objects.filter(teacher=teacher)

        for course in courses:
            revenue = course.enrolledcourse_set.aggregate(total_price=models.Sum('order_item__price'))['total_price'] or 0
            sales = course.enrolledcourse_set.count()

            courses_with_total_price.append({
                'course_image': course.image.url,
                'course_title': course.title,
                'revenue': revenue,
                'sales': sales
            })

        return Response(courses_with_total_price)


class TeacherCourseOrderListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CartOrderItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.CartOrderItem.objects.filter(teacher=teacher)
    
class TeacherQuestionAnswerAPIView(generics.ListAPIView):
    serializer_class = api_serializers.QuestionAnswerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Question_Answer.objects.filter(course__teacher=teacher)
    
class TeacherCouponListAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializers.CouponSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Coupon.objects.filter(teacher=teacher)
    
class TeacherCouponDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializers.CouponSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        coupon_id = self.kwargs['coupon_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Coupon.objects.get(teacher=teacher, id=coupon_id)
    
class TeacherNotificationListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Notification.objects.filter(teacher=teacher, seen=False)
    
class TeacherNotificationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializers.NotificationSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        notification_id = self.kwargs['notification_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        return api_models.Notification.objects.filter(teacher=teacher, id=notification_id)

class CourseCreateAPIView(generics.CreateAPIView):
    queryset = api_models.Course.objects.all()
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        course_instance = serializer.save()

        variant_data = []
        for key, value in self.request.data.items():
            if key.startswith('variant') and '[variant_title]' in key:
                index = key.split('[')[1].split(']')[0]
                title = value

                variant_data = {'title': title}
                item_data_list = []
                current_item = {}

                for item_key, item_value in self.request.data.item():
                    if f'variant[{index}][items]' in item_key:
                        field_name = item_key.split('[')[-1].split(']')[0]
                        if field_name == 'title':
                            if current_item:
                                item_data_list.append(current_item)
                            current_item = {}

                        current_item.update({field_name: item_value})

                if current_item:
                    item_data_list.append(current_item) 
                
                variant_data.append({'variant_data': variant_data, 'variant_item_data': item_data_list})

        for data_entry in variant_data:
            variant = api_models.Variant.objects.create(title=data_entry['variant_data']['title'], course=course_instance)

            for item_data in data_entry['variant_item_data']:
                preview_value = item_data.get('preview')
                preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                api_models.VariantItem.objects.create(
                    variant=variant,
                    title=item_data.get('title'),
                    description=item_data.get('description'),
                    file=item_data.get('file'),
                    preview=preview
                )

    def save_nested_data(self, course_instance, serializer_class, data):
        serializer = serializer_class(data=data, many=True, context={'course_instance': course_instance})
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course_instance)


class CourseUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = api_models.Course.objects.all()
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        course_id = self.kwargs['course_id']
        teacher = api_models.Teacher.objects.get(id=teacher_id)
        course = api_models.Course.objects.get(teacher=teacher, id=course_id)

        return course
    
    def update(self, request, *args, **kwargs):
        course = self.get_object()
        serializer = self.get_serializer(course, data=request.data)
        serializer.is_valid(raise_exception=True)

        if 'image' in request.data and isinstance(request.data['image'], InMemoryUploadedFile):
            course.image = request.data['image']
        elif 'image' in request.data and str(request.data['image']) == 'No File':
            course.image = None

        if 'file' in  request.data and not str(request.data['file']).startswith('http://'):
            course.file = request.data['file']

        if 'category' in request.data['category'] and request.data['category'] != 'NaN' and request.data['category'] != 'undefined':
            category = api_models.Category.objects.get(id=request.data['category'])
            course.category = category

        self.perform_update(serializer)
        self.update_variant(course, request.data)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_variant(self, course, request_data):
        for key, value in request_data.items():
            if key.startwith('variant') and '[variant_title]' in key:
                index = key.split('[')[1].split(']')[0]
                title = value

                id_key = f'variants[{index}][variant_id]'
                variant_id = request_data.get(id_key)

                variant_data = {'title': title}
                item_data_list = []
                current_item = {}

                for item_key, item_value in request_data.item():
                    if f'variant[{index}][items]' in item_key:
                        field_name = item_key.split('[')[-1].split(']')[0]
                        if field_name == 'title':
                            if current_item:
                                item_data_list.append(current_item)
                            current_item = {}

                        current_item.update({field_name: item_value})

                if current_item:
                    item_data_list.append(current_item) 
                
                variant_data.append({'variant_data': variant_data, 'variant_item_data': item_data_list})

                existing_variant = course.variant_set.filter(id=variant_id).first()

                if existing_variant:
                    existing_variant.title = title
                    existing_variant.save()

                    for item_data in item_data_list[1:]:
                        preview_value = item_data.get('preview')
                        preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                        variant_item = api_models.VariantItem.objects.filter(variant_item_id=item_data.get('variant_item_id')).first()

                        if not str(item_data.get('file')).startswith('http://'):
                            if item_data.get('file') != 'null':
                                file = item_data.get('file')
                            else:
                                file = None

                            title = item_data.get('title')
                            description = item_data.get('description')

                            if variant_item:
                                variant_item.title = title
                                variant_item.description = description
                                variant_item.file = file
                                variant_item.preview = preview
                            else:
                                variant_item = api_models.VariantItem.objects.create(
                                    variant=existing_variant,
                                    title=title,
                                    description=description,
                                    file=file,
                                    preview=preview
                                )
                        
                        else:
                            title = item_data.get('title')
                            description = item_data.get('description')

                            if variant_item:
                                variant_item.title = title
                                variant_item.description = description
                                variant_item.preview = preview
                            else:
                                variant_item = api_models.VariantItem.objects.create(
                                    variant=existing_variant,
                                    title=title,
                                    description=description,
                                    preview=preview
                                )

                        variant_item.save()
                else:
                    new_variant = api_models.Variant.objects.create(
                        course=course,
                        title=title
                    )

                    for item_data in item_data_list:
                        preview_value = item_data.get('preview')
                        preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                        api_models.VariantItem.objects.create(
                            variant=new_variant,
                            title=item_data.get('title'),
                            description=item_data.get('description'),
                            file=item_data.get('file'),
                            preview=preview
                        )

            else:
                pass



    def save_nested_data(self, course_instance, serializer_class, data):
        serializer = serializer_class(data=data, many=True, context={'course_instance': course_instance})
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course_instance)      

class TeacherCourseDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        course_id = self.kwargs['course_id']
        return api_models.Course.objects.get(course_id=course_id)
    
class TeacherCourseVariantDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializers.VariantSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        variant_id = self.kwargs['variant_id']
        teacher_id = self.kwargs['teacher_id']
        course_id = self.kwargs['course_id']

        teacher = api_models.Teacher.objects.get(id=teacher_id)
        course = api_models.Course.objects.get(teacher=teacher, course_id=course_id)
        return api_models.Variant.objects.get(variant_id=variant_id, course=course)
    

class TeacherCourseVariantItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializers.VariantItemSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        variant_id = self.kwargs['variant_id']
        variant_item_id = self.kwargs['variant_item_id']
        teacher_id = self.kwargs['teacher_id']
        course_id = self.kwargs['course_id']

        teacher = api_models.Teacher.objects.get(id=teacher_id)
        course = api_models.Course.objects.get(teacher=teacher, course_id=course_id)
        variant = api_models.Variant.objects.get(variant_id=variant_id, course=course)
        return api_models.VariantItem.objects.get(variant=variant, variant_item_id=variant_item_id)