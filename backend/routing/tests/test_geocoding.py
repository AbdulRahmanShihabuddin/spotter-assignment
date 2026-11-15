from unittest.mock import patch, MagicMock
from django.test import TestCase
from routing.services.geocoding import (
    PhotonGeocodingService,
    NominatimGeocodingService,
    MockGeocodingService,
    GeocodedLocation,
    geocode_location,
    _GEOCODE_CACHE,
)
from routing.exceptions import GeocodingNotFoundError, GeocodingError


class GeocodingTest(TestCase):
    def setUp(self):
        _GEOCODE_CACHE.clear()

    def test_mock_geocoding_known_location(self):
        mock_svc = MockGeocodingService()
        loc = mock_svc.geocode("Chicago, IL")
        self.assertEqual(loc.name, "Chicago, IL")
        self.assertAlmostEqual(loc.lat, 41.8781, places=3)
        self.assertAlmostEqual(loc.lon, -87.6298, places=3)

    def test_mock_geocoding_unknown_location(self):
        mock_svc = MockGeocodingService()
        with self.assertRaises(GeocodingNotFoundError):
            mock_svc.geocode("Atlantis Submerged City")

    def test_mock_geocoding_empty_query(self):
        mock_svc = MockGeocodingService()
        with self.assertRaises(GeocodingError):
            mock_svc.geocode("   ")

    @patch("requests.Session.get")
    def test_photon_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-96.7970, 32.7767],
                    },
                    "properties": {
                        "name": "Dallas",
                        "state": "Texas",
                        "country": "United States",
                    },
                }
            ],
        }
        mock_get.return_value = mock_resp

        svc = PhotonGeocodingService(user_agent="TestAgent/1.0")
        loc = svc.geocode("Dallas, TX")
        self.assertEqual(loc.name, "Dallas, TX")
        self.assertAlmostEqual(loc.lat, 32.7767)
        self.assertAlmostEqual(loc.lon, -96.7970)
        self.assertEqual(loc.display_name, "Dallas, Texas, United States")

    @patch("requests.Session.get")
    def test_photon_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "type": "FeatureCollection",
            "features": [],
        }
        mock_get.return_value = mock_resp

        svc = PhotonGeocodingService(user_agent="TestAgent/1.0")
        with self.assertRaises(GeocodingNotFoundError):
            svc.geocode("NonExistentPlaceXYZ123")

    @patch("requests.get")
    def test_geocode_location_helper_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-96.7970, 32.7767],
                    },
                }
            ],
        }
        mock_get.return_value = mock_resp

        result = geocode_location("Dallas, TX")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["lat"], 32.7767)
        self.assertAlmostEqual(result["lon"], -96.7970)

    @patch("requests.get")
    def test_geocode_location_helper_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "type": "FeatureCollection",
            "features": [],
        }
        mock_get.return_value = mock_resp

        result = geocode_location("NonExistent")
        self.assertIsNone(result)
