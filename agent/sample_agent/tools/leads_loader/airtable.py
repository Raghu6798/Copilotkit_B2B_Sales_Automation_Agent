from pyairtable import Table
from pyairtable.formulas import match
from .lead_loader_base import LeadLoaderBase
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_log, after_log

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type(Exception),
    before=before_log(logger, "INFO"),
    after=after_log(logger, "ERROR")
)
def _execute_with_retry(func, *args, **kwargs):
    return func(*args, **kwargs)

class AirtableLeadLoader(LeadLoaderBase):
    def __init__(self, access_token, base_id, table_name):
        # Use the access_token instead of api_key
        self.table = Table(access_token, base_id, table_name)

    def fetch_records(self, lead_ids=None, status_filter="NEW"):
        """
        Fetches leads from Airtable. If lead IDs are provided, fetch those specific records.
        Otherwise, fetch leads matching the given status.
        """
        if lead_ids:
            leads = []
            for lead_id in lead_ids:
                record = _execute_with_retry(self.table.get, lead_id)
                if record:
                    # Merge id and fields into a single dictionary
                    lead = {"id": record["id"], **record.get("fields", {})}
                    leads.append(lead)
            return leads
        else:
            # Fetch leads by status filter (based on "Status" field)
            # You can choose your own field for filter with different naming
            records = _execute_with_retry(self.table.all, formula=match({"Status": status_filter}))
            return [
                {"id": record["id"], **record.get("fields", {})}
                for record in records
            ]

    def update_record(self, lead_id, updates: dict):
        """
        Updates a record in Airtable, adding new fields dynamically if they don't exist.

        Args:
            lead_id (str): The ID of the record to update.
            updates (dict): A dictionary of fields to update or add.
        
        Returns:
            dict: The updated record from Airtable.
        """
        # Fetch the current record to ensure it exists and get its fields
        record = _execute_with_retry(self.table.get, lead_id)
        if not record:
            raise ValueError(f"Record with ID {lead_id} not found.")
        
        # Merge current fields with updates, adding any new fields
        current_fields = record.get("fields", {})
        updated_fields = {**current_fields, **updates}

        # Update the record in Airtable
        return _execute_with_retry(self.table.update, lead_id, updated_fields)

