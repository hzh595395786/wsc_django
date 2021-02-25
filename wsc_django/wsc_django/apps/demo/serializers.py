from rest_framework import serializers

class DemoSerializer(serializers.Serializer):

    realname = serializers.CharField()
    id = serializers.PrimaryKeyRelatedField(read_only=True)
