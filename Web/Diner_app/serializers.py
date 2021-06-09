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


class MatchSerializer(serializers.Serializer):
    """Your data serializer, define your fields here."""
    title_ue = serializers.CharField(max_length=3000)
    link_ue = serializers.CharField(max_length=3000)
    deliver_fee_ue = serializers.IntegerField()
    deliver_time_ue = serializers.IntegerField()
    choice_ue = serializers.BooleanField()
    uuid_ue = serializers.CharField(max_length=3000)
    triggered_at_ue = serializers.DateTimeField()
    menu_ue = serializers.ListField(required=False)
    budget_ue = serializers.IntegerField()
    rating_ue = serializers.FloatField()
    view_count_ue = serializers.FloatField()
    image_ue = serializers.CharField(max_length=3000)
    tags_ue = serializers.ListField()
    address_ue = serializers.CharField(max_length=3000)
    gps_ue = serializers.ListField()
    open_hours_ue = serializers.ListField()
    title_fp = serializers.CharField(max_length=3000)
    link_fp = serializers.CharField(max_length=3000)
    deliver_fee_fp = serializers.IntegerField()
    deliver_time_fp = serializers.IntegerField()
    choice_fp = serializers.BooleanField()
    uuid_fp = serializers.CharField(max_length=3000)
    triggered_at_fp = serializers.DateTimeField()
    menu_fp = serializers.ListField(required=False)
    budget_fp = serializers.IntegerField()
    rating_fp = serializers.FloatField()
    view_count_fp = serializers.FloatField()
    image_fp = serializers.CharField(max_length=3000)
    tags_fp = serializers.ListField()
    address_fp = serializers.CharField(max_length=3000)
    gps_fp = serializers.ListField()
    open_hours_fp = serializers.ListField()
    favorite = serializers.BooleanField()
    title_gm = serializers.CharField(max_length=3000, required=False)
    rating_gm = serializers.FloatField(required=False)
    view_count_gm = serializers.IntegerField(required=False)
    uuid_gm = serializers.CharField(max_length=3000, required=False)
    link_gm = serializers.CharField(max_length=3000, required=False)
    triggered_at_gm = serializers.DateTimeField(required=False)
    similarity = serializers.FloatField(required=False)
    cheaper_ue = serializers.ListField(required=False)
    cheaper_fp = serializers.ListField(required=False)
    not_found_gm = serializers.BooleanField(required=False)


class FilterSerializer(serializers.Serializer):
    """Your data serializer, define your fields here."""
    rating_ue = serializers.ListField()
    tags_ue = serializers.ListField()
    deliver_fee_ue = serializers.ListField()
    deliver_time_ue = serializers.ListField()
    budget_ue = serializers.ListField()
    view_count_ue = serializers.ListField()
    rating_fp = serializers.ListField()
    tags_fp = serializers.ListField()
    deliver_fee_fp = serializers.ListField()
    deliver_time_fp = serializers.ListField()
    budget_fp = serializers.ListField()
    view_count_fp = serializers.ListField()


class DashBoardSerializer(serializers.Serializer):
    states_metric_data = serializers.DictField()
    lambda_metric_data = serializers.DictField()
    trigger_log_data = serializers.DictField()