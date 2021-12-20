from RPA.Robocorp.Vault import Vault
from RPA.Tables import Tables
from RPA.Browser.Selenium import Selenium
from RPA.FileSystem import FileSystem
from RPA.PDF import PDF
from RPA.Archive import *
from RPA.HTTP import *
from RPA.Dialogs import *

ROBOT_STORE = "https://robotsparebinindustries.com/#/robot-order"
ORDERS_CSV = "https://robotsparebinindustries.com/orders.csv"


def return_vault_values():
    _secret = Vault().get_secret("credentials")
    USER_NAME = _secret["username"]
    PASSWORD = _secret["password"]
    return USER_NAME, PASSWORD


def show_finish_dialog(result):
    d = Dialogs()
    d.add_heading(heading=f'FINISH')
    d.add_text('The robot has finished work. \
                 Thank you for your time. \
                 You can download result file by click on button.')
    d.add_file('output/orders.zip')
    d.add_heading(heading=f'Your started text is:')
    d.add_text(result.dialogs[0].result()["text"])
    d.add_text(f'Executed with login: {return_vault_values()[0]}')
    d.run_dialog()


def show_start_dialog():
    d = Dialogs()
    d.add_heading(heading='START')
    d.add_text_input(name='text')
    d.add_text(text='Hello! \
                This is example of Robocorp Robot. \
                To start process push the button.  \
                See you soon.')
    d.run_dialog()
    d.wait_dialogs_as_completed()
    return d


def orderdes_as_table():
    HTTP().download(
        url=ORDERS_CSV,
        target_file=r'output/orders.csv'
    )
    return Tables().read_table_from_csv(
        r'output/orders.csv',
        columns=["Order number", "Head", "Body", "Legs", "Address"],
    )


def process_order(order, web):
    web.click_element("class:btn-dark")
    web.click_element(f'//*[@id="head"]/option[{str(int(order["Head"]) + 1)}]')
    web.click_element(f'//*[@id="id-body-{order["Body"]}"]')
    web.click_element('//div[3]/input')
    web.press_keys('//div[3]/input', order['Legs'])
    web.click_element('//div[4]/input')
    web.press_keys('name:address', order['Address'])
    web.click_element('id:preview')
    web.click_element('id:order')
    while not web.is_element_visible("xpath://div[@id='receipt']/h3"):
        web.click_element('id:order')
    web.wait_until_element_is_visible('//*[@id="robot-preview-image"]/img[1]')
    web.wait_until_element_is_visible('//*[@id="robot-preview-image"]/img[2]')
    web.wait_until_element_is_visible('//*[@id="robot-preview-image"]/img[3]')
    screenshot = web.capture_element_screenshot(
        "//div[@id='robot-preview-image']",
        f"output/{order['Order number']}.png"
    )
    receipt_html = web.get_element_attribute(
        "//div[@id='receipt']",
        "innerHTML"
    )
    PDF().html_to_pdf(
        receipt_html,
        f"output/receipts/{order['Order number']}.pdf"
    )
    PDF().add_files_to_pdf(
        files=[f"output/{order['Order number']}.png"],
        target_document=f"output/receipts/{order['Order number']}.pdf",
        append=True
    )
    web.reload_page()


def zip_receipts():
    Archive().archive_folder_with_zip(
        folder='output/receipts',
        archive_name='output/orders.zip'
    )


if __name__ == "__main__":
    result = show_start_dialog()
    web = Selenium()
    web.open_headless_chrome_browser(
        url=ROBOT_STORE
    )
    for order in orderdes_as_table():
        process_order(order, web)
    web.close_all_browsers()
    zip_receipts()
    show_finish_dialog(result)
