<?php

header('Content-Type: application/json');

$request_uri = $_SERVER['REQUEST_URI'];

if ($request_uri === '/payment') {
    $orders_api_host = getenv('ORDERS_API_HOST') ?: 'orders';
    $order_service_url = "http://{$orders_api_host}:3002/order";

    $orderJson = @file_get_contents($order_service_url);

    if ($orderJson === false) {
        http_response_code(503);
        echo json_encode(['error' => 'Order service is unavailable or returned an error.']);
        exit;
    }

    $orderData = json_decode($orderJson, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to decode order data.']);
        exit;
    }

    if (isset($orderData['error'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Failed to process payment due to an issue with the order.', 'order_details' => $orderData]);
        exit;
    }

    $transaction_id = 'txn_' . time() . '_' . bin2hex(random_bytes(4));

    $response = [
        'payment_status' => 'approved',
        'transaction_id' => $transaction_id,
        'order_details' => $orderData
    ];

    echo json_encode($response);

} else {
    http_response_code(404);
    echo json_encode(['error' => 'Endpoint not found. Please use /payment']);
}