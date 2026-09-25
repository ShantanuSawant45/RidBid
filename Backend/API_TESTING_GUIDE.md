
## Phase 1: Authentication
### 1. Register a Rider
*   **Method:** `POST`
*   **URL:** `http://localhost:8000/api/users/register/`
*   **Body (JSON):**
    ```json
    {
        "username": "rider_john",
        "email": "john@example.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "role": "rider",
        "phone_number": "+1234567890"
    }
    ```
*   **Action:** Click Send. Save the `access` token returned in the response as **RIDER_TOKEN**.

### 2. Register a Driver
*   **Method:** `POST`
*   **URL:** `http://localhost:8000/api/users/register/`
*   **Body (JSON):**
    ```json
    {
        "username": "driver_mike",
        "email": "mike@example.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "role": "driver",
        "phone_number": "+0987654321"
    }
    ```
*   **Action:** Click Send. Save the `access` token returned in the response as **DRIVER_TOKEN**.

---

## Phase 2: The Ride Lifecycle

### 3. Rider Requests a Ride
*   **Method:** `POST`
*   **URL:** `http://localhost:8000/api/rides/`
*   **Headers:** `Authorization: Bearer <RIDER_TOKEN>`
*   **Body (JSON):**
    ```json
    {
        "pickup_location": "POINT(78.4867 17.3850)",
        "pickup_address": "Charminar, Hyderabad",
        "dropoff_location": "POINT(78.3810 17.4399)",
        "dropoff_address": "Hitech City, Hyderabad",
        "vehicle_type": "sedan",
        "number_of_passengers": 2
    }
    ```
*   **Action:** Click Send. Save the `id` of the created ride from the response as **RIDE_ID**.

### 4. Driver Finds Nearby Rides (Geospatial Query)
*   **Method:** `GET`
*   **URL:** `http://localhost:8000/api/rides/nearby/?lat=17.385&lng=78.487&radius=5`
*   **Headers:** `Authorization: Bearer <DRIVER_TOKEN>`
*   **Action:** Click Send. The driver should see the ride requested by John in the response because it is within a 5km radius.

---

## Phase 3: Real-Time Bidding (The Wow Factor)

### 5. Rider Connects to WebSocket
*   **Tool:** In Postman, click **New > WebSocket Request**.
*   **URL:** `ws://localhost:8000/ws/rides/<RIDE_ID>/?token=<RIDER_TOKEN>`
    *(Replace `<RIDE_ID>` and `<RIDER_TOKEN>` with your actual values)*
*   **Action:** Click **Connect**. You should see "Connected" in the messages console.

### 6. Driver Submits a Bid
*   **Method:** `POST`
*   **URL:** `http://localhost:8000/api/bids/`
*   **Headers:** `Authorization: Bearer <DRIVER_TOKEN>`
*   **Body (JSON):**
    ```json
    {
        "ride": <RIDE_ID>,
        "amount": "250.00"
    }
    ```
*   **Action:** Click Send.

### 7. View Real-Time Update
*   **Action:** Immediately switch back to your WebSocket tab in Postman.
*   **Result:** You will see a JSON message automatically appear in the console. The rider was notified of the $250 bid instantly without having to refresh the page.

---

## Phase 4: Finalizing the Ride

### 8. Rider Accepts the Bid
*(First, check the response from Step 6 and copy the "id" of the bid as **BID_ID**)*
*   **Method:** `POST`
*   **URL:** `http://localhost:8000/api/bids/<BID_ID>/accept/`
*   **Headers:** `Authorization: Bearer <RIDER_TOKEN>`
*   **Body:** *(Empty JSON Body `{}`)*
*   **Action:** Click Send.

### 9. Verify Ride Status Update
*   **Method:** `GET`
*   **URL:** `http://localhost:8000/api/rides/<RIDE_ID>/`
*   **Headers:** `Authorization: Bearer <RIDER_TOKEN>`
*   **Action:** Click Send. In the response, notice that the `status` has changed from "bidding" to "accepted", and the `accepted_bid` field is now populated.

---
**Demo Complete!** This flow perfectly demonstrates your user authentication, PostGIS location querying, Django Channels real-time WebSockets, and database relationships.
