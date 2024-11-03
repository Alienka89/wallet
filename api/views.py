import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer

logger = logging.getLogger('api')


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.prefetch_related('transactions').all()
    permission_classes = [IsAuthenticated]
    serializer_class = WalletSerializer
    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    search_fields = ('label',)
    ordering_fields = ('label', 'balance')
    filterset_fields = ('label',)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related('wallet').all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = (
        DjangoFilterBackend,
        OrderingFilter,
    )
    search_fields = ('txid',)
    ordering_fields = ('amount', 'txid')
    filterset_fields = ['wallet', 'txid']

    def perform_create(self, serializer):
        super().perform_create(serializer)
        logger.info(f"Пользователь {self.request.user} создал транзакцию {serializer.instance.txid}")

    def perform_update(self, serializer):
        super().perform_update(serializer)
        logger.info(f"Пользователь {self.request.user} обновил транзакцию {serializer.instance.txid}")

    def perform_destroy(self, instance):
        txid = instance.txid
        super().perform_destroy(instance)
        logger.info(f"Пользователь {self.request.user} удалил транзакцию {txid}")
