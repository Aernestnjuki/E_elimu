from api import models as api_models
from userauths.serializers import ProfileSerializer
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

class CategorySerializer(ModelSerializer):

    class Meta:
        model = api_models.Category
        fields = ['title', 'image', 'slug', 'course_count']


class TeacherSerializer(ModelSerializer):
    class Meta:
        model = api_models.Teacher
        fields = [
            'user',
            'image',
            'full_name',
            'bio',
            'facebook',
            'twitter',
            'linkedin',
            'about',
            'country',
            'student',
            'courses',
            'review'
        ]

class VariantItemSerializer(serializers.ModelSerializer):

    # variant = serializers.PrimaryKeyRelatedField(queryset=api_models.Variant.objects.all())

    class Meta:
        model = api_models.VariantItem
        fields = ['variant_item_id', 'title', 'description', 'file', 'duration', 'content_duration', 'preview', 'date']

    def __init__(self, *args, **kwargs):
        super(VariantItemSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class VariantSerializer(ModelSerializer):

    variant_item = VariantItemSerializer(many=True)

    class Meta:
        model = api_models.Variant
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(VariantSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

    
        


class CompletedLessonSerializer(ModelSerializer):

    class Meta:
        model = api_models.Completedlesson
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CompletedLessonSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3


class NotesSerializer(ModelSerializer):

    class Meta:
        model = api_models.Notes
        fields = '__all__'

class QuestionAnswerMessageSerializer(ModelSerializer):

    profile = ProfileSerializer(many=False)

    class Meta:
        model = api_models.Question_Answer_Message
        fields = '__all__'

class QuestionAnswerSerializer(ModelSerializer):

    messages = QuestionAnswerMessageSerializer(many=True)
    profile = ProfileSerializer(many=False)

    class Meta:
        model = api_models.Question_Answer
        fields = '__all__'

class ReviewSerializer(ModelSerializer):

    profile = ProfileSerializer(many=False)

    class Meta:
        model = api_models.Review
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ReviewSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3


class EnrolledCourseSerializer(ModelSerializer):

    lectures = VariantItemSerializer(many=True, read_only=True)
    completed_lesson = CompletedLessonSerializer(many=True, read_only=True)
    curriculum = VariantSerializer(many=True, read_only=True)
    notes = NotesSerializer(many=True, read_only=True)
    question_answer = QuestionAnswerSerializer(many=True, read_only=True)
    review = ReviewSerializer(many=False, read_only=True)

    class Meta:
        model = api_models.EnrolledCourse
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super(EnrolledCourseSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3






class CourseSerializer(ModelSerializer):
    
    students = EnrolledCourseSerializer(many=True, required=False, read_only=True)
    curriculum = VariantSerializer(many=True, required=False, read_only=True)
    Lectures = VariantItemSerializer(many=True, required=False, read_only=True)
    reviews = ReviewSerializer(many=True, required=False, read_only=True)

    # print('Variant', curriculum)

    # print('*' * 100)

    # print('VariantItem', Lectures)

    class Meta:
        model = api_models.Course
        fields = [
            "id",
            "category",
            'teacher',
            "file",
            "image",
            "title",
            "description",
            "price",
            "language",
            "level",
            "platform_status",
            "teacher_course_status",
            "featured",
            "course_id",
            "slug",
            "date",
            "students",
            "curriculum",
            "Lectures",
            "average_rating",
            "rating_count",
            "reviews"
        ]

   
    def __init__(self, *args, **kwargs):
        super(CourseSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3
        


class CartSerializer(ModelSerializer):

    class Meta:
        model = api_models.Cart
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CartSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3


class CartOrderItemSerializer(ModelSerializer):

    class Meta:
        model = api_models.CartOrderItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CartOrderItemSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

class CartOrderSerializer(ModelSerializer):

    order_items = CartOrderItemSerializer(many=True)

    class Meta:
        model = api_models.CartOrder
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CartOrderSerializer, self).__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "POST":
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3


class CertificateSerializer(ModelSerializer):

    class Meta:
        model = api_models.Certificate
        fields = '__all__'


class NotificationSerializer(ModelSerializer):

    class Meta:
        model = api_models.Notification
        fields = '__all__'

class CouponSerializer(ModelSerializer):

    class Meta:
        model = api_models.Coupon
        fields = '__all__'

class WishListSerializer(ModelSerializer):

    class Meta:
        model = api_models.WishList
        fields = '__all__'


class CountrySerializer(ModelSerializer):

    class Meta:
        model = api_models.Country
        fields = '__all__'


class StudentSerializer(serializers.Serializer):
    total_courses = serializers.IntegerField(default=0)
    completed_lessons = serializers.IntegerField(default=0)
    achived_certificates = serializers.IntegerField(default=0)

class TeacherSummarySerializer(serializers.Serializer):
    total_courses = serializers.IntegerField(default=0)
    total_students = serializers.IntegerField(default=0)
    total_revenue = serializers.IntegerField(default=0)
    monthly_revenue = serializers.IntegerField(default=0)