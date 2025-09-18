"""
DHIS2 Integration Service for Healthcare Data Exchange.

This module provides comprehensive integration with DHIS2 (District Health Information System 2)
for surveillance data reporting, organization unit management, and health system interoperability.
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urljoin

import aiohttp

logger = logging.getLogger(__name__)


class DHIS2Client:
    """
    DHIS2 client for health information system integration.

    Provides comprehensive functionality for connecting to DHIS2 instances,
    managing authentication, and exchanging surveillance data.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int = 30
    ):
        """
        Initialize DHIS2 client.

        Args:
            base_url: DHIS2 instance URL
            username: DHIS2 username
            password: DHIS2 password
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = None
        self.auth_token = None
        self.session_expires = None
        logger.info(f"DHIS2 client initialized for {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()

    async def _create_session(self) -> None:
        """Create HTTP session with authentication."""
        if self.session is None:
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=self.timeout)

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                auth=aiohttp.BasicAuth(self.username, self.password)
            )

            # Test authentication
            await self.authenticate()
            logger.info("DHIS2 session created successfully")

    async def _close_session(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("DHIS2 session closed")

    async def authenticate(self) -> bool:
        """
        Authenticate with DHIS2 system.

        Returns:
            bool: True if authentication successful
        """
        try:
            url = urljoin(self.base_url, '/api/me')

            if not self.session:
                await self._create_session()

            async with self.session.get(url) as response:
                if response.status == 200:
                    user_info = await response.json()
                    self.auth_token = user_info.get('id')
                    self.session_expires = datetime.now() + timedelta(hours=1)
                    logger.info(f"Authenticated as user: {user_info.get('displayName', 'Unknown')}")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def get_organization_units(
        self,
        parent_id: str | None = None,
        level: int | None = None,
        fields: str = "id,name,level,parent"
    ) -> list[dict[str, Any]]:
        """
        Get organization units from DHIS2.

        Args:
            parent_id: Parent organization unit ID
            level: Organization unit level
            fields: Fields to retrieve

        Returns:
            List of organization units
        """
        try:
            url = urljoin(self.base_url, '/api/organisationUnits')
            params = {'fields': fields, 'paging': 'false'}

            if parent_id:
                params['filter'] = f'parent.id:eq:{parent_id}'
            if level:
                params['filter'] = f'level:eq:{level}'

            if not self.session:
                await self._create_session()

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    org_units = data.get('organisationUnits', [])
                    logger.info(f"Retrieved {len(org_units)} organization units")
                    return org_units
                else:
                    logger.error(f"Failed to get organization units: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error retrieving organization units: {e}")
            return []

    async def get_data_sets(self, fields: str = "id,name,periodType") -> list[dict[str, Any]]:
        """
        Get available data sets from DHIS2.

        Args:
            fields: Fields to retrieve

        Returns:
            List of data sets
        """
        try:
            url = urljoin(self.base_url, '/api/dataSets')
            params = {'fields': fields, 'paging': 'false'}

            if not self.session:
                await self._create_session()

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    data_sets = data.get('dataSets', [])
                    logger.info(f"Retrieved {len(data_sets)} data sets")
                    return data_sets
                else:
                    logger.error(f"Failed to get data sets: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error retrieving data sets: {e}")
            return []

    async def submit_data_values(
        self,
        data_set_id: str,
        org_unit_id: str,
        period: str,
        data_values: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Submit data values to DHIS2.

        Args:
            data_set_id: DHIS2 data set ID
            org_unit_id: Organization unit ID
            period: Reporting period
            data_values: Data values to submit

        Returns:
            Submission result
        """
        try:
            url = urljoin(self.base_url, '/api/dataValueSets')

            payload = {
                "dataSet": data_set_id,
                "orgUnit": org_unit_id,
                "period": period,
                "dataValues": data_values
            }

            if not self.session:
                await self._create_session()

            async with self.session.post(url, json=payload) as response:
                result = await response.json()

                if response.status == 200:
                    logger.info(f"Successfully submitted {len(data_values)} data values")
                    return {
                        "status": "success",
                        "import_count": result.get('importCount', {}),
                        "conflicts": result.get('conflicts', []),
                        "response": result
                    }
                else:
                    logger.error(f"Data submission failed: {response.status}")
                    return {
                        "status": "error",
                        "error": result,
                        "status_code": response.status
                    }

        except Exception as e:
            logger.error(f"Error submitting data values: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_data_elements(
        self,
        data_set_id: str | None = None,
        fields: str = "id,name,valueType"
    ) -> list[dict[str, Any]]:
        """
        Get data elements from DHIS2.

        Args:
            data_set_id: Filter by data set ID
            fields: Fields to retrieve

        Returns:
            List of data elements
        """
        try:
            url = urljoin(self.base_url, '/api/dataElements')
            params = {'fields': fields, 'paging': 'false'}

            if data_set_id:
                params['filter'] = f'dataSetElements.dataSet.id:eq:{data_set_id}'

            if not self.session:
                await self._create_session()

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    data_elements = data.get('dataElements', [])
                    logger.info(f"Retrieved {len(data_elements)} data elements")
                    return data_elements
                else:
                    logger.error(f"Failed to get data elements: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error retrieving data elements: {e}")
            return []

    async def validate_data_set(
        self,
        data_set_id: str,
        org_unit_id: str,
        period: str
    ) -> dict[str, Any]:
        """
        Validate data set completion for a specific period.

        Args:
            data_set_id: DHIS2 data set ID
            org_unit_id: Organization unit ID
            period: Reporting period

        Returns:
            Validation result
        """
        try:
            url = urljoin(self.base_url, '/api/completeDataSetRegistrations')
            params = {
                'dataSet': data_set_id,
                'orgUnit': org_unit_id,
                'period': period
            }

            if not self.session:
                await self._create_session()

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    registrations = data.get('completeDataSetRegistrations', [])

                    is_complete = len(registrations) > 0
                    completion_date = None

                    if is_complete:
                        completion_date = registrations[0].get('date')

                    return {
                        "is_complete": is_complete,
                        "completion_date": completion_date,
                        "registrations": registrations
                    }
                else:
                    logger.error(f"Validation failed: {response.status}")
                    return {"is_complete": False, "error": "Validation failed"}

        except Exception as e:
            logger.error(f"Error validating data set: {e}")
            return {"is_complete": False, "error": str(e)}


class DHIS2DataMapper:
    """
    Data mapper for converting surveillance data to DHIS2 format.

    Provides mapping functionality for transforming malaria surveillance data
    into DHIS2-compatible data structures and formats.
    """

    def __init__(self):
        """Initialize DHIS2 data mapper with standard mappings."""
        self.data_element_mappings = {
            # Malaria case data elements
            "suspected_cases": "DE_MAL_SUSP",
            "confirmed_cases": "DE_MAL_CONF",
            "severe_cases": "DE_MAL_SEV",
            "deaths": "DE_MAL_DEATH",

            # Laboratory data elements
            "rdt_performed": "DE_RDT_PERF",
            "rdt_positive": "DE_RDT_POS",
            "microscopy_performed": "DE_MIC_PERF",
            "microscopy_positive": "DE_MIC_POS",

            # Vector control data elements
            "nets_distributed": "DE_NET_DIST",
            "houses_sprayed": "DE_IRS_HOUSES",
            "breeding_sites_treated": "DE_LSM_SITES",

            # Age/sex disaggregation
            "cases_under_5": "DE_MAL_U5",
            "cases_over_5": "DE_MAL_O5",
            "cases_pregnant": "DE_MAL_PREG"
        }

        self.category_option_mappings = {
            "male": "CO_MALE",
            "female": "CO_FEMALE",
            "under_5": "CO_U5",
            "over_5": "CO_O5"
        }

        logger.info("DHIS2 data mapper initialized")

    def map_surveillance_report(
        self,
        report_data: dict[str, Any],
        org_unit_id: str,
        data_set_id: str = "MAL_WEEKLY_001"
    ) -> dict[str, Any]:
        """
        Map surveillance report to DHIS2 data value set format.

        Args:
            report_data: Surveillance report data
            org_unit_id: Organization unit ID
            data_set_id: DHIS2 data set ID

        Returns:
            DHIS2-formatted data value set
        """
        logger.info(f"Mapping surveillance report {report_data.get('report_id', 'unknown')}")

        # Extract period from reporting period
        period = self._format_period(report_data.get("reporting_period", {}))

        # Map case data to data values
        data_values = []
        case_data = report_data.get("case_data", {})

        for field, value in case_data.items():
            if field in self.data_element_mappings and value is not None:
                data_values.append({
                    "dataElement": self.data_element_mappings[field],
                    "value": str(value)
                })

        # Add age/sex disaggregated data if available
        if "age_breakdown" in case_data:
            age_breakdown = case_data["age_breakdown"]
            data_values.extend(self._map_age_disaggregation(age_breakdown))

        # Add vector control data if available
        vector_data = report_data.get("vector_data", {})
        for field, value in vector_data.items():
            if field in self.data_element_mappings and value is not None:
                data_values.append({
                    "dataElement": self.data_element_mappings[field],
                    "value": str(value)
                })

        dhis2_data = {
            "dataSet": data_set_id,
            "orgUnit": org_unit_id,
            "period": period,
            "dataValues": data_values,
            "completeDate": datetime.now().isoformat()
        }

        logger.info(f"Mapped {len(data_values)} data values for DHIS2 submission")
        return dhis2_data

    def _format_period(self, reporting_period: dict[str, Any]) -> str:
        """
        Format reporting period for DHIS2.

        Args:
            reporting_period: Reporting period data

        Returns:
            DHIS2-formatted period string
        """
        start_date = reporting_period.get("start_date")
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        elif start_date is None:
            start_date = datetime.now()

        # Format as weekly period (e.g., 2023W52)
        year = start_date.year
        week = start_date.isocalendar()[1]

        return f"{year}W{week:02d}"

    def _map_age_disaggregation(self, age_breakdown: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Map age-disaggregated data to DHIS2 format.

        Args:
            age_breakdown: Age-disaggregated case data

        Returns:
            List of DHIS2 data values
        """
        data_values = []

        if "under_5" in age_breakdown:
            data_values.append({
                "dataElement": self.data_element_mappings["cases_under_5"],
                "value": str(age_breakdown["under_5"])
            })

        if "over_5" in age_breakdown:
            data_values.append({
                "dataElement": self.data_element_mappings["cases_over_5"],
                "value": str(age_breakdown["over_5"])
            })

        if "pregnant_women" in age_breakdown:
            data_values.append({
                "dataElement": self.data_element_mappings["cases_pregnant"],
                "value": str(age_breakdown["pregnant_women"])
            })

        return data_values


class DHIS2Service:
    """
    High-level DHIS2 service for healthcare data integration.

    Provides convenient methods for common DHIS2 operations including
    surveillance data export, organization management, and data validation.
    """

    def __init__(self, client: DHIS2Client):
        """
        Initialize DHIS2 service.

        Args:
            client: Configured DHIS2 client
        """
        self.client = client
        self.mapper = DHIS2DataMapper()
        self._org_units_cache = {}
        self._data_sets_cache = {}
        logger.info("DHIS2 service initialized")

    async def export_surveillance_report(
        self,
        report_data: dict[str, Any],
        org_unit_id: str,
        data_set_id: str = "MAL_WEEKLY_001"
    ) -> dict[str, Any]:
        """
        Export surveillance report to DHIS2.

        Args:
            report_data: Surveillance report data
            org_unit_id: Organization unit ID
            data_set_id: DHIS2 data set ID

        Returns:
            Export result with status and details
        """
        logger.info(f"Exporting surveillance report {report_data.get('report_id', 'unknown')}")

        try:
            # Map data to DHIS2 format
            dhis2_data = self.mapper.map_surveillance_report(
                report_data, org_unit_id, data_set_id
            )

            # Submit to DHIS2
            result = await self.client.submit_data_values(
                data_set_id=dhis2_data["dataSet"],
                org_unit_id=dhis2_data["orgUnit"],
                period=dhis2_data["period"],
                data_values=dhis2_data["dataValues"]
            )

            if result["status"] == "success":
                logger.info("Surveillance report exported successfully")
                return {
                    "status": "success",
                    "dhis2_import_id": f"IMP_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "records_imported": len(dhis2_data["dataValues"]),
                    "conflicts": result.get("conflicts", []),
                    "import_summary": result.get("import_count", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Failed to export surveillance report: {result}")
                return {
                    "status": "error",
                    "error": result.get("error", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error exporting surveillance report: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_organization_hierarchy(
        self,
        root_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get organization unit hierarchy from DHIS2.

        Args:
            root_id: Root organization unit ID

        Returns:
            Organization hierarchy structure
        """
        logger.info("Retrieving organization hierarchy")

        try:
            # Get all organization units
            org_units = await self.client.get_organization_units(
                fields="id,name,level,parent,children"
            )

            # Build hierarchy structure
            hierarchy = self._build_org_hierarchy(org_units, root_id)

            # Cache results
            self._org_units_cache = {org["id"]: org for org in org_units}

            logger.info(f"Retrieved organization hierarchy with {len(org_units)} units")
            return hierarchy

        except Exception as e:
            logger.error(f"Error retrieving organization hierarchy: {e}")
            return {}

    def _build_org_hierarchy(
        self,
        org_units: list[dict[str, Any]],
        root_id: str | None = None
    ) -> dict[str, Any]:
        """Build hierarchical organization structure."""
        org_dict = {org["id"]: org for org in org_units}

        def build_tree(unit_id: str) -> dict[str, Any]:
            unit = org_dict.get(unit_id, {})
            children = unit.get("children", [])

            return {
                "id": unit.get("id"),
                "name": unit.get("name"),
                "level": unit.get("level"),
                "children": [build_tree(child["id"]) for child in children] if children else []
            }

        # Find root units (no parent or specific root)
        if root_id:
            return build_tree(root_id)
        else:
            root_units = [org for org in org_units if not org.get("parent")]
            return {
                "roots": [build_tree(org["id"]) for org in root_units]
            }

    async def validate_export_readiness(
        self,
        org_unit_id: str,
        data_set_id: str,
        period: str
    ) -> dict[str, Any]:
        """
        Validate if organization unit is ready for data export.

        Args:
            org_unit_id: Organization unit ID
            data_set_id: Data set ID
            period: Reporting period

        Returns:
            Validation result with readiness status
        """
        logger.info(f"Validating export readiness for {org_unit_id}")

        try:
            # Check if organization unit exists
            org_units = await self.client.get_organization_units(
                fields="id,name,level"
            )
            org_unit = next((org for org in org_units if org["id"] == org_unit_id), None)

            if not org_unit:
                return {
                    "ready": False,
                    "error": "Organization unit not found",
                    "details": {}
                }

            # Check if data set exists
            data_sets = await self.client.get_data_sets()
            data_set = next((ds for ds in data_sets if ds["id"] == data_set_id), None)

            if not data_set:
                return {
                    "ready": False,
                    "error": "Data set not found",
                    "details": {"org_unit": org_unit}
                }

            # Check data completeness
            completion_status = await self.client.validate_data_set(
                data_set_id, org_unit_id, period
            )

            return {
                "ready": True,
                "org_unit": org_unit,
                "data_set": data_set,
                "completion_status": completion_status,
                "validated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error validating export readiness: {e}")
            return {
                "ready": False,
                "error": str(e),
                "details": {}
            }

    async def get_system_info(self) -> dict[str, Any]:
        """
        Get DHIS2 system information.

        Returns:
            System information and capabilities
        """
        try:
            # Test connectivity and get basic info
            authenticated = await self.client.authenticate()

            if not authenticated:
                return {
                    "status": "disconnected",
                    "error": "Authentication failed"
                }

            # Get system capabilities
            org_units = await self.client.get_organization_units()
            data_sets = await self.client.get_data_sets()

            return {
                "status": "connected",
                "base_url": self.client.base_url,
                "authenticated": True,
                "capabilities": {
                    "organization_units": len(org_units),
                    "data_sets": len(data_sets),
                    "last_sync": datetime.now().isoformat()
                },
                "connection_test": "passed"
            }

        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                "status": "error",
                "error": str(e),
                "connection_test": "failed"
            }


# Convenience function for creating DHIS2 service
async def create_dhis2_service(
    base_url: str,
    username: str,
    password: str
) -> DHIS2Service:
    """
    Create and initialize DHIS2 service.

    Args:
        base_url: DHIS2 instance URL
        username: DHIS2 username
        password: DHIS2 password

    Returns:
        Initialized DHIS2 service
    """
    client = DHIS2Client(base_url, username, password)
    await client._create_session()

    service = DHIS2Service(client)
    logger.info("DHIS2 service created and ready")

    return service
