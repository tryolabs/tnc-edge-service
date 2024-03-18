
The elog data is split into 3 major categories: Trip Details, ETP Event, and Longline Event. There is 1 Trip Details Event per trip. There is 1 Longline Event per set+haul. There is any number of ETP Events per trip.

Notes:
- all IDs are uuids
- all dates&times are in "unix time" format, which is "the amount of time, in seconds, after 1970". These are easily convertable to human-readable dates&times.


Trip Details Event
- this comes from the "begin trip" button.
- contains basic boat/captain/flag administrative info
- contains some fishery-specific equipment info
- contains an ipad photo of the gear used this trip (barrel of hooks)

ETP Event
- this comes from its own "report etp" button.
- contains info that the captain reports about etp

Longline Event
- this comes from the "start set, end set, start haul, end haul" workflow.
- contains 4 automatically captured gps+datetime points - start_set, end_set, start_haul, end_haul
- Potentially stores 2 values for each of those 4 gps+datetime points
    - the automatically captured datapoint (system)
    - the edited datapoint when the captain updates the value (user)
- list of catch species
- list of bycatch species, with additional info like "weight"
- metadata about catch edits, a list of what the captain changed and when
- metadata about bycatch edits, a list of what the captain changed and when

```
{
    "eventType": "tripDetailsEvent",
    "eventId": "<unique id>",
    "tripId": "<unique for the trip>",
    "dateTime": 1704568080,
    "lastCompletedTimestamp": 1707219061.44202,
    "captainName": "Juan Venegas.arguello",
    "vesselName": "Saint Patrick",
    "flagState": "Costa Rica",
    "nationalBoatIdNumber": "PQ 1533",
    "gearPhoto": "<jpeg photo data>",
    "hooks": "Circular hook",
    "numberOfHooks": 750,
    "wireLeads": "No"
}
```

```
{
    "eventId": "<unique id>",
    "tripId": "<unique for the trip>",
    "lastCompletedTimestamp": 1690456949.372511, 
    "items": [
    {
        "amount": 1,
        "condition": "Viva",
        "dateTime": 1689096817.762138,
        "latitude": 7.87721,
        "longitude": -89.66997,
        "species": "Mobula spp."
    },
    {
        "amount": 2,
        "dateTime": 1689620908.916417,
        "latitude": 9.26127,
        "longitude": -88.58167,
        "species": "Chelonia mydas"
    },
    ]
}
```

```
{
    "eventType": "longlineEvent",
    "eventId": "<unique for this set/haul>",
    "tripId": "<unique for the trip>",
    "lastCompletedTimestamp": 1708193556.615646,
    "locationData": {
        "startSetModifiedByUser": false,
        "endSetModifiedByUser": false,
        "startHaulModifiedByUser": false,
        "endHaulModifiedByUser": false,
        "systemStartSetDateTime": 1708106771.321401,
        "systemStartSetLatitude": 7.97504,
        "systemStartSetLongitude": -87.33628,
        "systemEndSetDateTime": 1708120866.353774,
        "systemEndSetLatitude": 7.94548,
        "systemEndSetLongitude": -86.92834,
        "systemStartHaulDateTime": 1708169664.370867,
        "systemStartHaulLatitude": 7.89461,
        "systemStartHaulLongitude": -86.66596,
        "systemEndHaulDateTime": 1708192992.408557,
        "systemEndHaulLatitude": 7.89857,
        "systemEndHaulLongitude": -86.75769,
        "userStartSetDateTime": null,
        "userStartSetLatitude": null,
        "userStartSetLongitude": null,
        "userEndSetDateTime": null,
        "userEndSetLatitude": null,
        "userEndSetLongitude": null,
        "userStartHaulDateTime": null,
        "userStartHaulLatitude": null,
        "userStartHaulLongitude": null,
        "userEndHaulDateTime": null,
        "userEndHaulLatitude": null,
        "userEndHaulLongitude": null
    },
    "catch": [
        {
            "amount": 6,
            "species": "Coryphaena hippurus"
        },
        {
            "amount": 3,
            "species": "Xiphias gladius"
        },
        {
            "amount": 1,
            "species": "Istiophorus platypterus"
        },
        {
            "amount": 3,
            "species": "Carcharhinus falciformis"
        }
    ],
    "bycatch": [
        {
            "centimetres": 2,
            "kilograms": 0,
            "species": "Testudines"
        }
    ],
    "catchEdits": [
        {
            "change": 0,
            "species": "Coryphaena hippurus",
            "timestamp": 1708193479.106751
        },
        {
            "change": 6,
            "species": "Coryphaena hippurus",
            "timestamp": 1708193486.009575
        },
        {
            "change": 0,
            "species": "Xiphias gladius",
            "timestamp": 1708193492.82156
        },
        {
            "change": 3,
            "species": "Xiphias gladius",
            "timestamp": 1708193504.725975
        },
        {
            "change": 0,
            "species": "Istiophorus platypterus",
            "timestamp": 1708193524.397781
        },
        {
            "change": 1,
            "species": "Istiophorus platypterus",
            "timestamp": 1708193528.667675
        },
        {
            "change": 0,
            "species": "Carcharhinus falciformis",
            "timestamp": 1708193532.202324
        },
        {
            "change": 3,
            "species": "Carcharhinus falciformis",
            "timestamp": 1708193536.909904
        }
    ],
    "bycatchEdits": [
        {
            "change": {
            "cm": 0,
            "kg": 0
            },
            "itemId": 0,
            "species": "Testudines",
            "timestamp": 1708193545.563922
        },
        {
            "change": {
            "cm": 2,
            "kg": 0
            },
            "itemId": 0,
            "species": "Testudines",
            "timestamp": 1708193552.554468
        }
    ]
}
```

