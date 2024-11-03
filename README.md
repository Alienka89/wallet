# Usage

## Build and start the services:

### bash
    docker compose build
    docker compose up

### Applying Migrations
    docker compose exec wallet_web python manage.py migrate

### Creating a Superuser
    docker compose exec wallet_web python manage.py createsuperuser

### Run test
    docker compose exec wallet_web python manage.py test


http://localhost:8004/admin/


# API Endpoints
The API adheres to the JSON specification.

## Wallets
    List Wallets: GET /api/wallets/
    Create Wallet: POST /api/wallets/
    Retrieve Wallet: GET /api/wallets/{id}/
    Update Wallet: PATCH /api/wallets/{id}/
    Delete Wallet: DELETE /api/wallets/{id}/
## Transactions
    List Transactions: GET /api/transactions/
    Create Transaction: POST /api/transactions/
    Retrieve Transaction: GET /api/transactions/{id}/
    Update Transaction: PATCH /api/transactions/{id}/
    Delete Transaction: DELETE /api/transactions/{id}/
## Features
- Pagination: Use page query parameter.
- Filtering: Use query parameters like ?wallet={wallet_id}.
- Sorting: Use ordering query parameter, e.g., ?ordering=amount.
