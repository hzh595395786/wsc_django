from rest_framework import serializers

class DemoSerializer(serializers.Serializer):

    shop_code = serializers.CharField()
