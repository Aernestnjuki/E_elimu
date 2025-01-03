from django.urls import path

from userauths import views as auth_views
from api import views as api_view

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('user/token', auth_views.MyTokenObtainPairView.as_view()),
    path('user/token/refresh/', TokenRefreshView.as_view()),
    path('user/register/', auth_views.RegisterView.as_view()),
    path('user/password-change/', auth_views.PasswordChangeAPIView.as_view()),
    path('user/password-reset/<email>/', auth_views.PasswordResetEmailVerifyAPIView.as_view()),
    path('user/change-reset-password/', auth_views.ChangePasswordAPIView.as_view()),

    # core urls
    path('course/category/', api_view.CategoryListAPIView.as_view()),
    path('course/course-list/', api_view.CourseListAPIView.as_view()),
    path('course/course-detail/<slug>/', api_view.CourseDetailAPIView.as_view()),
    path('course/cart/', api_view.CartAPIView.as_view()),
    path('course/cart-list/', api_view.CartListAPIView.as_view()),
    path('course/cart-item-delete/<cart_id>/<item_id>/', api_view.CartItemDeleteAPIView.as_view()),
    path('course/search/', api_view.SearchCourseAPIView.as_view()),
    path('course/test', api_view.your_view),

    # cart
    path('order/cart-stats/<user_id>/', api_view.CartStatsAPIView.as_view()),
    path('order/create-order/', api_view.CreateOrderAPIView.as_view()),
    path('order/checkout/<oid>/', api_view.CheckOutAPIView.as_view()),
    path('order/coupon/', api_view.CouponApplyAPIView.as_view()),

    #payment
    path('payment/stripe-checkout/<order_oid>/', api_view.StripeCheckOutAPIView.as_view()),
    path('payment/success/', api_view.PaymentSuccessAPIView.as_view()),

    # student
    path('student/summary/<user_id>/', api_view.StudentSummaryAPIView.as_view()),
    path('student/course-list/<user_id>/', api_view.StudentCourseListAPIView.as_view()),
    path('student/course-detail/<user_id>/<enrollment_id>/', api_view.StudentCourseDetailAPIView.as_view()),
    path('student/course-completed/', api_view.StudentCourseCompletedCreateAPIView.as_view()),
    path('student/course-note/<user_id>/<enrollment_id>/', api_view.StudentCreateNoteAPIView.as_view()),
    path('student/course-note-detail/<user_id>/<enrollment_id>/<note_id>/', api_view.StudentNoteDetailAPIView.as_view()),
    path('student/rate-course/', api_view.StudentRateCourseCreateAPIView.as_view()),
    path('student/review-detail/<user_id>/<review_id>/', api_view.StudentRateCourseUpdateAPIView.as_view()),
    path('student/wishlist/<user_id>/', api_view.StudentWishListListCreateAPIView.as_view()),
    path('student/question-answer-list-create/<course_id>/', api_view.QuestionAnswerListCreateAPIView.as_view()),
    path('student/question-answer-message-create/', api_view.QuestionAnswerMessageSendAPIView.as_view()),

    # teacher
    path('teacher/summary/<teacher_id>/', api_view.TeacherSummaryAPIView.as_view()),
    path('teacher/course-list/<teacher_id>/', api_view.TeacherCourseListView.as_view()),
    path('teacher/review-list/<teacher_id>/', api_view.TeacherReviewListAPIView.as_view()),
    path('teacher/review-detail/<teacher_id>/<review_id>/', api_view.TeacherReviewDetailAPIView.as_view()),
    path('teacher/student-list/<teacher_id>/', api_view.TeacherStudentListAPIView.as_view({'get': 'list'})),

    path('teacher/monthly-earning/<teacher_id>/', api_view.TeacherALlMonthEarningAPIView),
    path('teacher/best-selling-course/<teacher_id>/', api_view.TeacherBestSellingCourseAPIView.as_view({'get': 'list'})),
    path('teacher/course-order-list/<teacher_id>/', api_view.TeacherCourseOrderListAPIView.as_view()),
    path('teacher/question-answer-list/<teacher_id>/', api_view.TeacherQuestionAnswerAPIView.as_view()),
    path('teacher/coupon-list/<teacher_id>/', api_view.TeacherCouponListAPIView.as_view()),
    path('teacher/coupon-detail/<teacher_id>/<coupon_id>/', api_view.TeacherCouponDetailAPIView.as_view()),
    path('teacher/notification-list/<teacher_id>/', api_view.TeacherNotificationListAPIView.as_view()),
    path('teacher/notification-detail/<teacher_id>/<notification_id>/', api_view.TeacherNotificationDetailAPIView.as_view()),
    path('teacher/course-create/', api_view.CourseCreateAPIView.as_view()),
    path('teacher/course-update/<teacher_id>/<course_id>/', api_view.CourseUpdateAPIView.as_view()),
    path('teacher/course/detail/<course_id>/', api_view.TeacherCourseDetailAPIView.as_view()),
    path('teacher/course/variant-delete/<variant_id>/<teacher_id>/<course_id>/', api_view.TeacherCourseVariantDeleteAPIView.as_view()),
    path('teacher/course/variant-item-delete/<variant_id>/<variant_item_id>/<teacher_id>/<course_id>/', api_view.TeacherCourseVariantItemDeleteAPIView.as_view()),
]


