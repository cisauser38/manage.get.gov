"""Data migration: Send domain invitations once to existing customers."""

import argparse
import json
import logging

from django.core.management import BaseCommand
from registrar.management.commands.utility.extra_transition_domain_helper import OrganizationDataLoader
from registrar.management.commands.utility.terminal_helper import TerminalColors, TerminalHelper
from registrar.management.commands.utility.transition_domain_arguments import TransitionDomainArguments
from registrar.models import TransitionDomain
from registrar.models.domain import Domain
from registrar.models.domain_information import DomainInformation
from django.core.paginator import Paginator
from typing import List

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send domain invitations once to existing customers."

    def add_arguments(self, parser):
        """Add command line arguments."""

        parser.add_argument(
            "migration_json_filename",
            help=("A JSON file that holds the location and filenames" "of all the data files used for migrations"),
        )

        parser.add_argument("--sep", default="|", help="Delimiter character")

        parser.add_argument("--debug", action=argparse.BooleanOptionalAction)

        parser.add_argument("--directory", default="migrationdata", help="Desired directory")

        parser.add_argument(
            "--domain_additional_filename",
            help="Defines the filename for additional domain data",
        )

        parser.add_argument(
            "--organization_adhoc_filename",
            help="Defines the filename for domain type adhocs",
        )

    def handle(self, migration_json_filename, **options):
        """Process the objects in TransitionDomain."""

        # === Parse JSON file === #
        # Desired directory for additional TransitionDomain data
        # (In the event they are stored seperately)
        directory = options["directory"]
        # Add a slash if the last character isn't one
        if directory and directory[-1] != "/":
            directory += "/"

        json_filepath = directory + migration_json_filename

        # If a JSON was provided, use its values instead of defaults.
        with open(json_filepath, "r") as jsonFile:
            # load JSON object as a dictionary
            try:
                data = json.load(jsonFile)
                # Create an instance of TransitionDomainArguments
                # Iterate over the data from the JSON file
                for key, value in data.items():
                    if value is not None and value.strip() != "":
                        options[key] = value
            except Exception as err:
                logger.error(
                    f"{TerminalColors.FAIL}"
                    "There was an error loading "
                    "the JSON responsible for providing filepaths."
                    f"{TerminalColors.ENDC}"
                )
                raise err
        # === End parse JSON file === #
        args = TransitionDomainArguments(**options)

        changed_fields = [
            "address_line",
            "city",
            "state_territory",
            "zipcode",
        ]
        proceed = TerminalHelper.prompt_for_execution(
            system_exit_on_terminate=True,
            info_to_inspect=f"""
            ==Master data file==
            domain_additional_filename: {args.domain_additional_filename}

            ==Organization name information==
            organization_adhoc_filename: {args.organization_adhoc_filename}

            ==Containing directory==
            directory: {args.directory}

            ==Proposed Changes==
            For each TransitionDomain, modify the following fields: {changed_fields}
            """,
            prompt_title="Do you wish to load organization data for TransitionDomains?",
        )

        if not proceed:
            return None

        logger.info(f"{TerminalColors.MAGENTA}" "Loading organization data onto TransitionDomain tables...")
        load = OrganizationDataLoader(args)
        domain_information_to_update = load.update_organization_data_for_all()

        # Reprompt the user to reinspect before updating DomainInformation
        proceed = TerminalHelper.prompt_for_execution(
            system_exit_on_terminate=True,
            info_to_inspect=f"""
            ==Master data file==
            domain_additional_filename: {args.domain_additional_filename}

            ==Organization name information==
            organization_adhoc_filename: {args.organization_adhoc_filename}

            ==Containing directory==
            directory: {args.directory}

            ==Proposed Changes==
            Number of DomainInformation objects to change: {len(domain_information_to_update)}
            """,
            prompt_title="Do you wish to load organization data for DomainInformation?",
        )

        if not proceed:
            return None

        if len(domain_information_to_update) == 0:
            logger.error(f"{TerminalColors.MAGENTA}" "No DomainInformation objects exist" f"{TerminalColors.ENDC}")
            return None

        logger.info(
            f"{TerminalColors.MAGENTA}"
            "Preparing to load organization data onto DomainInformation tables..."
            f"{TerminalColors.ENDC}"
        )
        self.update_domain_information(domain_information_to_update, args.debug)

    def update_domain_information(self, desired_objects: List[TransitionDomain], debug):
        di_to_update = []
        di_failed_to_update = []
        di_skipped = []

        # Grab each TransitionDomain we want to change.
        transition_domains = TransitionDomain.objects.filter(
            username__in=[item.username for item in desired_objects],
            domain_name__in=[item.domain_name for item in desired_objects],
        ).distinct()

        if len(desired_objects) != len(transition_domains):
            raise Exception("Could not find all desired TransitionDomains")

        # Then, for each domain_name grab the associated domain object.
        domains = Domain.objects.filter(name__in=[td.domain_name for td in transition_domains])
        # Create dictionary for faster lookup
        domains_dict = {d.name: d for d in domains}

        # Start with all DomainInformation objects
        filtered_domain_informations = DomainInformation.objects.all()

        # Then, use each domain object to map domain <--> DomainInformation
        # Fetches all DomainInformations in one query.
        # If any related organization fields have been updated,
        # we can assume that they modified this information themselves - thus we should not update it.
        domain_informations = filtered_domain_informations.filter(
            domain__in=domains,
            address_line1__isnull=True,
            city__isnull=True,
            state_territory__isnull=True,
            zipcode__isnull=True,
        )

        domain_informations_dict = {di.domain.name: di for di in domain_informations}

        for item in transition_domains:
            if item.domain_name not in domains_dict:
                logger.error(f"Could not add {item.domain_name}. Domain does not exist.")
                di_failed_to_update.append(item)
                continue

            current_domain = domains_dict[item.domain_name]
            if current_domain.name not in domain_informations_dict:
                logger.info(
                    f"{TerminalColors.YELLOW}"
                    f"Domain {current_domain.name} was updated by a user. Cannot update."
                    f"{TerminalColors.ENDC}"
                )
                di_skipped.append(item)
                continue

            # Based on the current domain, grab the right DomainInformation object.
            current_domain_information = domain_informations_dict[current_domain.name]

            # Update fields
            current_domain_information.address_line1 = item.address_line
            current_domain_information.city = item.city
            current_domain_information.state_territory = item.state_territory
            current_domain_information.zipcode = item.zipcode

            di_to_update.append(current_domain_information)
            if debug:
                logger.info(f"Updated {current_domain.name}...")

        if di_failed_to_update:
            failed = [item.domain_name for item in di_failed_to_update]
            logger.error(
                f"""{TerminalColors.FAIL}
                Failed to update. An exception was encountered on the following TransitionDomains: {failed}
                {TerminalColors.ENDC}"""
            )
            raise Exception("Failed to update DomainInformations")

        if di_skipped:
            logger.info(f"Skipped updating {len(di_skipped)} fields. User-supplied data exists")

        self.bulk_update_domain_information(di_to_update, debug)

    def bulk_update_domain_information(self, di_to_update, debug):
        if debug:
            logger.info(f"Updating these TransitionDomains: {[item for item in di_to_update]}")

        logger.info(f"Ready to update {len(di_to_update)} TransitionDomains.")

        logger.info(f"{TerminalColors.MAGENTA}" "Beginning mass DomainInformation update..." f"{TerminalColors.ENDC}")

        changed_fields = [
            "address_line1",
            "city",
            "state_territory",
            "zipcode",
        ]

        batch_size = 1000
        # Create a Paginator object. Bulk_update on the full dataset
        # is too memory intensive for our current app config, so we can chunk this data instead.
        paginator = Paginator(di_to_update, batch_size)
        for page_num in paginator.page_range:
            page = paginator.page(page_num)
            DomainInformation.objects.bulk_update(page.object_list, changed_fields)

        if debug:
            logger.info(f"Updated these DomainInformations: {[item for item in di_to_update]}")

        logger.info(
            f"{TerminalColors.OKGREEN}" f"Updated {len(di_to_update)} DomainInformations." f"{TerminalColors.ENDC}"
        )
