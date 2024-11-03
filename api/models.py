import logging
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger('api')


class Wallet(models.Model):
    label = models.CharField(max_length=255)
    balance = models.DecimalField(
        max_digits=36, decimal_places=18, default=Decimal('0.0')
    )

    class Meta:
        ordering = ['-id']

    def update_balance(self):
        # Блокируем запись кошелька для предотвращения состояния гонки
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(pk=self.pk)
            total = wallet.transactions.aggregate(
                total_amount=Sum('amount')
            )['total_amount'] or Decimal('0.0')

            if total < 0:
                raise ValueError("Balance cannot be negative.")

            wallet.balance = total
            wallet.save()

    def __str__(self):
        return self.label


class Transaction(models.Model):
    wallet = models.ForeignKey(
        Wallet, related_name='transactions', on_delete=models.CASCADE
    )
    txid = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(
        max_digits=36, decimal_places=18
    )

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self.pk is None
            super().save(*args, **kwargs)
            self.wallet.update_balance()
            action = "Создана" if is_new else "Обновлена"
            logger.info(f"{action} транзакция {self.txid} на сумму {self.amount} для кошелька {self.wallet.id}")

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            super().delete(*args, **kwargs)
            self.wallet.update_balance()
            logger.info(f"Удалена транзакция {self.txid} для кошелька {self.wallet.id}")

    def __str__(self):
        return f"{self.txid}: {self.amount}"


@receiver(post_save, sender=Transaction)
def log_transaction(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Транзакция {instance.txid} создана для кошелька {instance.wallet.id}")
