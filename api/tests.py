from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.models import Wallet, Transaction


class WalletAPITestCase(TestCase):
    """Тесты для API кошельков"""

    def setUp(self):
        self.client = APIClient()
        # Создаём пользователя и авторизуем его
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.wallet = Wallet.objects.create(label='Test Wallet')

    def test_create_wallet(self):
        """Тест создания нового кошелька"""
        data = {
            "data": {
                "type": "Wallet",
                "attributes": {
                    "label": "New Wallet"
                }
            }
        }
        response = self.client.post(
            reverse('wallet-list'),
            data,
            format='vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Wallet.objects.count(), 2)
        self.assertEqual(Wallet.objects.first().label, 'New Wallet')

    def test_get_wallet_list(self):
        """Тест получения списка кошельков"""
        response = self.client.get(
            reverse('wallet-list'),
            HTTP_ACCEPT='application/vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['label'], 'Test Wallet')

    def test_wallet_detail(self):
        """Тест получения деталей кошелька"""
        response = self.client.get(
            reverse('wallet-detail', kwargs={'pk': self.wallet.pk}),
            HTTP_ACCEPT='application/vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['label'], 'Test Wallet')
        # Проверяем наличие поля transactions
        self.assertIn('transactions', response.data)

    def test_wallet_balance_never_negative(self):
        """Тест, что баланс кошелька никогда не может быть отрицательным"""
        # Попытаемся создать транзакцию, ведущую к отрицательному балансу
        data = {
            "data": {
                "type": "Transaction",
                "attributes": {
                    "txid": "tx_negative",
                    "amount": '-100.0'
                },
                "relationships": {
                    "wallet": {
                        "data": {
                            "type": "Wallet",
                            "id": str(self.wallet.id)
                        }
                    }
                }
            }
        }
        response = self.client.post(
            reverse('transaction-list'),
            data,
            format='vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Balance cannot be negative.', str(response.data))


class TransactionAPITestCase(TestCase):
    """Тесты для API транзакций"""

    def setUp(self):
        self.client = APIClient()
        # Создаём пользователя и авторизуем его
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.wallet = Wallet.objects.create(label='Test Wallet')

    def test_create_transaction(self):
        """Тест создания транзакции"""
        data = {
            "data": {
                "type": "Transaction",
                "attributes": {
                    "txid": "tx1",
                    "amount": '100.0'
                },
                "relationships": {
                    "wallet": {
                        "data": {
                            "type": "Wallet",
                            "id": str(self.wallet.id)
                        }
                    }
                }
            }
        }
        response = self.client.post(
            reverse('transaction-list'),
            data,
            format='vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('100.0'))

    def test_create_transaction_zero_amount(self):
        """Тест создания транзакции с нулевой суммой"""
        data = {
            "data": {
                "type": "Transaction",
                "attributes": {
                    "txid": "tx_zero",
                    "amount": '0.0'
                },
                "relationships": {
                    "wallet": {
                        "data": {
                            "type": "Wallet",
                            "id": str(self.wallet.id)
                        }
                    }
                }
            }
        }
        response = self.client.post(
            reverse('transaction-list'),
            data,
            format='vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Сумма транзакции не может быть равна нулю.', str(response.data))

    def test_unique_txid(self):
        """Тест уникальности поля txid"""
        Transaction.objects.create(wallet=self.wallet, txid='tx1', amount=Decimal('50.0'))
        data = {
            "data": {
                "type": "Transaction",
                "attributes": {
                    "txid": "tx1",  # тот же txid
                    "amount": '100.0'
                },
                "relationships": {
                    "wallet": {
                        "data": {
                            "type": "Wallet",
                            "id": str(self.wallet.id)
                        }
                    }
                }
            }
        }
        response = self.client.post(
            reverse('transaction-list'),
            data,
            format='vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('transaction with this txid already exists', str(response.data).lower())

    def test_transaction_detail(self):
        """Тест получения деталей транзакции"""
        transaction = Transaction.objects.create(wallet=self.wallet, txid='tx1', amount=Decimal('50.0'))
        response = self.client.get(
            reverse('transaction-detail', kwargs={'pk': transaction.pk}),
            HTTP_ACCEPT='application/vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['txid'], 'tx1')
        self.assertEqual(Decimal(response.data['amount']), Decimal('50.0'))

    def test_pagination(self):
        """Тест пагинации списка транзакций"""
        # Создаём несколько транзакций
        for i in range(15):
            Transaction.objects.create(wallet=self.wallet, txid=f'tx{i}', amount=Decimal('10.0'))
        response = self.client.get(
            reverse('transaction-list'),
            HTTP_ACCEPT='application/vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        # Проверяем, что возвращается только 10 записей (PAGE_SIZE = 10)
        self.assertEqual(len(response.data['results']), 10)

    def test_ordering(self):
        """Тест сортировки списка транзакций"""
        Transaction.objects.create(wallet=self.wallet, txid='tx1', amount=Decimal('50.0'))
        Transaction.objects.create(wallet=self.wallet, txid='tx2', amount=Decimal('100.0'))
        response = self.client.get(
            reverse('transaction-list'),
            {'sort': '-amount'},
            HTTP_ACCEPT='application/vnd.api+json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['results'][0]['amount']), Decimal('100.0'))


class WalletModelTestCase(TestCase):
    """Тесты для модели Wallet"""

    def test_wallet_creation(self):
        wallet = Wallet.objects.create(label='Test Wallet')
        self.assertEqual(wallet.label, 'Test Wallet')
        self.assertEqual(wallet.balance, Decimal('0.0'))


class TransactionModelTestCase(TestCase):
    """Тесты для модели Transaction"""

    def setUp(self):
        self.wallet = Wallet.objects.create(label='Test Wallet')

    def test_transaction_creation(self):
        transaction = Transaction.objects.create(wallet=self.wallet, txid='tx1', amount=Decimal('100.0'))
        self.assertEqual(transaction.txid, 'tx1')
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('100.0'))

    def test_negative_balance_prevented(self):
        with self.assertRaises(ValueError):
            Transaction.objects.create(wallet=self.wallet, txid='tx1', amount=Decimal('-100.0'))

    def test_balance_updates(self):
        Transaction.objects.create(wallet=self.wallet, txid='tx1', amount=Decimal('100.0'))
        Transaction.objects.create(wallet=self.wallet, txid='tx2', amount=Decimal('-30.0'))
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('70.0'))
