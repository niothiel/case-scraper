import datetime

import scrapy
from scrapy.http.request.form import FormRequest


COURT_NAME = 'Fairfax County General District Court'
COURT_CODE = '059'


class CaseSpider(scrapy.Spider):
    name = "cases"

    def start_requests(self):
        urls = [
            "https://eapps.courts.state.va.us/gdcourts/captchaVerification.do"
        ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_verification)

    def save_response(self, response):
        page = response.url.split('/')[-2]
        filename = f'cases-{page}.html'
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log(f'Saved file {filename}')

    def parse_verification(self, response):
        yield FormRequest.from_response(
            response,
            callback=self.after_accept_verification
        )

    def after_accept_verification(self, response):
        # Select the court.
        yield FormRequest.from_response(
            response,
            formdata={
                'selectedCourtsName': COURT_NAME,
                'selectedCourtsFipCode': COURT_CODE,
            },
            callback=self.after_court_select,
        )

    def after_court_select(self, response):
        # Navigate to the "Hearing Date Search"
        link = response.xpath('//a[text() = "Hearing Date Search"]/@href')[0].get()
        self.log(f"Referred log: {link}")

        yield response.follow(link, callback=self.after_hearing_date_search)

    def after_hearing_date_search(self, response):
        date = datetime.date(year=2021, month=10, day=6)
        yield FormRequest.from_response(
            response,
            formname='caseSearchForm',
            formdata={
                'searchTerm': date.strftime('%m/%d/%Y'),
            },
            callback=self.on_case_search_page,
            cb_kwargs={
                'date': date,
            }
        )

    def on_case_search_page(self, response, date=None, page=1):
        self.log(f"Processing search page for date: {date} (page: {page})")

        # Get all case links
        case_links = response.xpath('//table[@class="tableborder"]//a/@href')

        if case_links:
            self.log(f"Got {len(case_links)} cases for date: {date} (page: {page})")
        else:
            self.log(f"Got no case links for date: {date} (page: {page})!")

        # Enqueue pagination
        if case_links:
            request = FormRequest.from_response(
                response,
                formname='caseSearchForm',
                formdata={
                    'formAction': 'caseDetails',
                    'searchCategory': None,
                    'caseSearch': None,
                    'caseInfoScrollForward': 'Next',
                },
                callback=self.on_case_search_page,
                dont_filter=True,
                cb_kwargs={
                    'date': date,
                    'page': page + 1,
                }
            )
            self.log(f"Next page request: {request._body}")
            yield request
        else:
            # Current page done, go back one.
            previous_date = date - datetime.timedelta(days=1)
            self.log(f"Enqueueing processing of date: {previous_date}")
            delta = datetime.date.today() - previous_date
            if delta.days < 366:
                request = FormRequest.from_response(
                    response,
                    formname='caseSearchForm',
                    formdata={
                        'searchTerm': previous_date.strftime('%m/%d/%Y'),
                        'caseSearch': 'Search',
                        'searchCategory': None,
                        'unCheckedCases': '',
                    },
                    callback=self.on_case_search_page,
                    cb_kwargs={
                        'date': previous_date,
                    },
                )
                self.log(f"Hearing date request body: {request._body}")
                yield request

        # Process case links directly and first (it's LIFO ordered)
        for case_link in case_links:
            yield response.follow(
                case_link,
                callback=self.on_case_details,
                cb_kwargs={
                    'date': date,
                }
            )

    def extract_from_table(self, response, name):
        selectors = response.xpath(f'//td[contains(text(), "{name}")]/following-sibling::td/text()')
        if not selectors:
            raise ValueError("Could not find field:", name)

        value = selectors[0].get().strip().replace('\n', '\\n')
        return value if value else None

    def on_case_details(self, response, date=None):
        # self.save_response(response)

        yield {
            'case_number': self.extract_from_table(response, 'Case Number'),
            'filed_date': self.extract_from_table(response, 'Filed Date'),
            'court_date': date.isoformat(),
            'locality': self.extract_from_table(response, 'Locality'),
            'name': self.extract_from_table(response, 'Name'),
            'status': self.extract_from_table(response, 'Status'),
            'defense_attorney': self.extract_from_table(response, 'Defense Attorney'),
            'address': self.extract_from_table(response, 'Address'),
            'aka1': self.extract_from_table(response, 'AKA1'),
            'aka2': self.extract_from_table(response, 'AKA2'),
            'gender': self.extract_from_table(response, 'Gender'),
            'race': self.extract_from_table(response, 'Race'),
            'dob': self.extract_from_table(response, 'DOB'),
            'charge': self.extract_from_table(response, 'Charge'),
            'code_section': self.extract_from_table(response, 'Code Section'),
            'case_type': self.extract_from_table(response, 'Case Type'),
            'class': self.extract_from_table(response, 'Class'),
            'offense_date': self.extract_from_table(response, 'Offense Date'),
            'arrest_date': self.extract_from_table(response, 'Arrest Date'),
            'complainant': self.extract_from_table(response, 'Complainant'),
            'amended_charge': self.extract_from_table(response, 'Amended Charge'),
            'amended_code': self.extract_from_table(response, 'Amended Code'),
            'amended_case_type': self.extract_from_table(response, 'Amended Case Type'),
            'final_disposition': self.extract_from_table(response, 'Final Disposition'),
            'fine': self.extract_from_table(response, 'Fine'),
            'costs': self.extract_from_table(response, 'Costs'),
            'fine_costs_due': self.extract_from_table(response, 'Fine/Costs Due'),
            'fine_costs_paid': self.extract_from_table(response, 'Fine/Costs Paid'),
            'fine_costs_paid_date': self.extract_from_table(response, 'Fine/Costs Paid Date'),
            'VASAP': self.extract_from_table(response, 'VASAP'),
        }
