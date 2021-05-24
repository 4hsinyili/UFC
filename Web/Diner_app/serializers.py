from rest_framework import serializers


class UESerializer(serializers.Serializer):
    """Your data serializer, define your fields here."""
    title = serializers.CharField(max_length=3000)
    link = serializers.CharField(max_length=3000)
    deliver_fee = serializers.IntegerField()
    deliver_time = serializers.CharField(max_length=3000)
    UE_choice = serializers.BooleanField()
    uuid = serializers.CharField(max_length=3000)
    triggered_at = serializers.DateTimeField()
    menu = serializers.ListField()
    budget = serializers.IntegerField()
    rating = serializers.FloatField()
    view_count = serializers.FloatField()
    image = serializers.CharField(max_length=3000)
    tags = serializers.ListField()
    address = serializers.CharField(max_length=3000)
    gps = serializers.ListField()
    open_hours = serializers.ListField()


class FPSerializer(serializers.Serializer):
    """Your data serializer, define your fields here."""
    title = serializers.CharField(max_length=3000)
    link = serializers.CharField(max_length=3000)
    deliver_fee = serializers.IntegerField()
    deliver_time = serializers.CharField(max_length=3000)
    FP_choice = serializers.BooleanField()
    uuid = serializers.CharField(max_length=3000)
    triggered_at = serializers.DateTimeField()
    menu = serializers.ListField()
    budget = serializers.IntegerField()
    rating = serializers.FloatField()
    view_count = serializers.FloatField()
    image = serializers.CharField(max_length=3000)
    tags = serializers.ListField()
    address = serializers.CharField(max_length=3000)
    gps = serializers.ListField()
    open_hours = serializers.ListField()


class GMSerializer(serializers.Serializer):
    """Your data serializer, define your fields here."""
    title = serializers.CharField(max_length=3000)
    link = serializers.CharField(max_length=3000)
    triggered_at = serializers.DateTimeField()
    budget = serializers.IntegerField()
    rating = serializers.FloatField()
    view_count = serializers.FloatField()
    address = serializers.CharField(max_length=3000)
    reviews = serializers.ListField()


class UnionSerializer(serializers.Serializer):
    """Your data serializer, define your fields here."""
    title = serializers.CharField(max_length=3000)
    link = serializers.CharField(max_length=3000)
    triggered_at = serializers.DateTimeField()
    budget = serializers.IntegerField()
    rating = serializers.FloatField()
    view_count = serializers.FloatField()
    address = serializers.CharField(max_length=3000)
    reviews = serializers.ListField()


class FilterSerializer(serializers.Serializer):
    """Your data serializer, define your fields here."""
    rating = serializers.ListField()
    tags = serializers.ListField()
    deliver_fee = serializers.ListField()
    deliver_time = serializers.ListField()
    budget = serializers.ListField()
    view_count = serializers.ListField()
    open_days = serializers.ListField()
