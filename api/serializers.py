from rest_framework.exceptions import ValidationError
from rest_framework_json_api import serializers

from .models import Wallet, Transaction


class TransactionSerializerShort(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'txid', 'amount')




class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'wallet', 'txid', 'amount')

    def validate(self, data):
        wallet = data.get('wallet') or self.instance.wallet
        amount = data.get('amount') or self.instance.amount
        new_balance = wallet.balance + amount
        if new_balance < 0:
            raise serializers.ValidationError({
                'amount': 'Balance cannot be negative.'
            })
        return data

    def validate_amount(self, value):
        if value == 0:
            raise ValidationError("Сумма транзакции не может быть равна нулю.")
        return value

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))


class WalletSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializerShort(
        many=True,
        read_only=True
    )

    class Meta:
        model = Wallet
        fields = ('id', 'label', 'balance', 'transactions')
