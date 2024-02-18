import time
import sys
from PyQt5.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QDate
import pandas as pd
from playwright.sync_api import sync_playwright

def load_web(URL, df, dates):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        time.sleep(6)
        try:
            alert_page = page.query_selector("//div[@class='b-pv3 alert-warn']")
        except:
            alert_page = True

        room_locator = None
        if alert_page is True or alert_page is not None:
            try:
                alert_text = alert_page.inner_text()
                # TODO: handle it if needed.
            except:
                try:
                    room_locator = page.locator('.room-rate-card')
                except Exception as e:
                    pass
        else:
            try:
                room_locator = page.locator('.room-rate-card')
            except Exception as e:
                    pass
        
        data = []
        if room_locator:
            title = page.locator('.hotel-detail-header-title-row').inner_text()
            for i in range(room_locator.count()):
                item = room_locator.nth(i)
                try:
                    room_type = item.locator('.room-title').inner_text()
                    points = item.locator('.points-rate').inner_text()
                    if 'Standard Room Free Night\n' not in points:
                        continue
                    points = points.replace('Standard Room Free Night\n', '')
                    check_in = dates[0]
                    check_out = dates[1]
                    data.append((check_in, check_out, title, room_type, points))
                except Exception as e:
                    print(e)
        else:
            data = []
            check_in = dates[0]
            check_out = dates[1]
            data.append((check_in, check_out, 'None', 'None', 'None'))

        new_df =pd.DataFrame(data, columns=['Check-in', 'Check-out', 'Hotel', 'Room type', 'Points'])
        df = pd.concat([df, new_df], ignore_index=True)
        browser.close()
    return df

class Form(QtWidgets.QDialog):
    #Initialize and Show UI
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = uic.loadUi("main.ui")
        self.ui.show()
        self.ui.start_date.setDate(QDate.currentDate())
        self.ui.end_date.setDate(QDate.currentDate())
        self.ui.go_button.clicked.connect(self.go_button_click)

    #Basically everything done here

    def get_dates_list_string(self):
        dates_list_string =[]
        start_date=self.ui.start_date.date()
        end_date=self.ui.end_date.date()
        consec_nights = self.ui.consec_nights.value()

        if start_date == end_date:
            dates_list_string.append((start_date.toString("yyyy-MM-dd"), start_date.addDays(consec_nights).toString("yyyy-MM-dd")))
            
        else:
            while(start_date <= end_date):
                dates_list_string.append((start_date.toString("yyyy-MM-dd"), start_date.addDays(consec_nights).toString("yyyy-MM-dd")))
                start_date = start_date.addDays(1)

        return dates_list_string
    def get_URL_concat(self, item):
            URL = []
            URL.append('https://www.hyatt.com/shop/')
            URL.append(''.join(filter(str.isalpha, self.ui.hotel_code.text().lower())))
            URL.append('?rooms=1&adults=1&checkinDate=')
            URL.append(item[0])
            URL.append('&checkoutDate=')
            URL.append(item[1])
            URL.append('&kids=0&accessibilityCheck=false&rateFilter=woh')
            return ''.join(URL)

    def sanitary_check(self):
        start_date=self.ui.start_date.date()
        end_date=self.ui.end_date.date()
        s = self.ui.hotel_code.text()

        if start_date.addDays(30) < end_date:
            QMessageBox.critical(self, "Error",  "Cannot search longer than 1 month")
            return 1        
        if start_date > end_date:
            QMessageBox.critical(self, "Error", "Start date should be the same with or earlier than End date")
            return 1        
        if len(s)!=5:
            QMessageBox.critical(self, "Error", "Hotel code should be 5 alphabet letters")
            return 1
        if len(''.join(filter(str.isalpha, s)))!=5:
            QMessageBox.critical(self, "Error", "Hotel code should be 5 alphabet letters")
            return 1
        return 0


    def go_button_click(self):
        self.ui.go_button.setDisabled(True)
        error = self.sanitary_check()
        if error == 1:
            self.ui.go_button.setEnabled(True)
            return
        dates_list_string = self.get_dates_list_string()

        df=pd.DataFrame()
        for item in dates_list_string:
            URL_concat = self.get_URL_concat(item)
            df = load_web(URL_concat, df, item)

        self.tableWidget = QTableWidget()
        self.tableWidget.setWindowTitle("Search Result")
        self.tableWidget.setColumnCount(len(df.columns))
        self.tableWidget.setRowCount(len(df.index))
        for i in range(len(df.index)):
           for j in range(len(df.columns)):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))
        self.tableWidget.setHorizontalHeaderLabels(df.columns)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.tableWidget.show()
        self.ui.go_button.setEnabled(True)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = Form()
    sys.exit(app.exec())


