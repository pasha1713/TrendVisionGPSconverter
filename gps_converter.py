import argparse
import datetime
import sys
from geopy.distance import geodesic
from datetime import datetime

def calculate_checksum(sentence):
    """
    Расчет контрольной суммы для NMEA-0183 сообщения
    """
    filtered_sentence = sentence.strip('$').strip('*')
    checksum = 0
    for s in filtered_sentence:
        checksum ^= ord(s)
    return "{:02X}".format(checksum)

def print_help():
    """
    Выводит информацию о использовании скрипта
    """
    print("Этот скрипт был разработан совместно мной R2ARZ и моим помощником, AI-ассистентом. Скрипт")
    print("предназначен для обработки данных GPS и преобразования их в формат NMEA-0183.")
    print("Использование скрипта:")
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Скрипт запущен как exe-файл
        print("1. Запустите скрипт командой 'gps_converter.exe <in_file.txt'")
    else:
        # Скрипт запущен как py-файл
        print("1. Запустите скрипт командой 'python gps_converter.py <in_file.txt'")
    print("2. Введите данные GPS в формате:")
    print("A20221110020351,5533.567871,N,3709.591309,E,57.70,63.06,0,-1,8,0.000000")
    print("3. После ввода каждой строки скрипт будет выводить сообщение в формате NMEA-0183.")

prev_lat = None
prev_lon = None
prev_time = None

# Создаем парсер аргументов командной строки
parser = argparse.ArgumentParser()
parser.add_argument('input_file', help='Входной файл')
parser.add_argument('--output', help='Маска имени выходного файла')
args = parser.parse_args()

if not sys.stdin.isatty():
    for line in sys.stdin:
        # Обработка строки с координатами                                                                             
        data = line.strip().split(',')                                                                                
        time = data[0][9:]                                                                                            
        time_str = f'{time[:2]}{time[2:4]}{time[4:]}.{"0" * 3}'                                                       
        lat_deg = int(data[1][:2])                                                                                    
        lat_min = float(data[1][2:])                                                                                  
        lat = lat_deg + lat_min / 60                                                                                  
        if data[2] == 'S':                                                                                            
            lat = -lat                                                                                                
        lon_deg = int(data[3][:2])                                                                                    
        lon_min = float(data[3][2:])                                                                                  
        lon = lon_deg + lon_min / 60                                                                                  
        if data[4] == 'W':                                                                                            
            lon = -lon                                                                                                
        # Преобразование координат в формат DDMM.MMMM и DDDMM.MMMM                                                    
        lat_dd = int(lat)                                                                                             
        lat_mm = (lat - lat_dd) * 60                                                                                  
        lat_ddmm = f'{lat_dd:02d}{lat_mm:.4f}'                                                                        
        lon_dd = int(lon)                                                                                             
        lon_mm = (lon - lon_dd) * 60                                                                                  
        lon_ddmm = f'{lon_dd:03d}{lon_mm:07.4f}'                                                                      
    
        curr_time = datetime.strptime(data[0], 'A%Y%m%d%H%M%S')                                                      
        if prev_lat is not None and prev_lon is not None and prev_time is not None:                                  
            distance = geodesic((prev_lat, prev_lon), (lat, lon)).meters                                             
            time_diff = (curr_time - prev_time).total_seconds()                                                      
            speed = distance / time_diff * 1.94384  # перевод в узлы                                                 
#            speed = '{:.6f}'.format(speed)  # ограничение точности до 6 символов после запятой                       
            precision = 2  # количество символов после запятой                                                           
            format_str = '{{:.{}f}}'.format(precision)                                                                   
            formatted_speed = format_str.format(speed)                                                                   
        else:                                                                                                        
#            speed = 0.0                                                                                              
            speed = data[5]                                                                                              
            # Преобразуем дату в формат YYYYMMDD_HHMMSS
            date = datetime.datetime.strptime(data[0], 'A%Y%m%d%H%M%S')
            date_string = date.strftime('%Y%m%d_%H%M%S')

            # Создаем имя выходного файла на основе маски, если она была указана
            if args.output:
                output_filename = args.output.replace('%s', date_string)
            else:
                output_filename = None

        direction = f'{float(data[6]):.6f}'                                                                          
        prev_lat = lat                                                                                               
        prev_lon = lon                                                                                               
        prev_time = curr_time                                                                                        

        date_str = f'{data[0][7:9]}{data[0][5:7]}{data[0][3:5]}'                                                      
        # Формирование сообщений NMEA-0183                                                                            
        rmc_template = '$GPRMC,{time},A,{lat},{lat_dir},{lon},{lon_dir},{speed},{direction},{date},,*{checksum}'      
        rmc_message = rmc_template.format(time=time_str, lat=lat_ddmm, lat_dir=data[2], lon=lon_ddmm, lon_dir=data[4],
                                          speed=speed, direction=data[6], date=date_str, mode='A',                  
                                          checksum=calculate_checksum(rmc_template.format(time=time_str,              
                                          lat=lat_ddmm, lat_dir=data[2], lon=lon_ddmm, lon_dir=data[4],               
                                          speed=speed, direction=data[6], date=date_str, mode='A', checksum='')))   
#        rmc_message = rmc_template.format(time=time_str, lat=lat_ddmm, lat_dir=data[2], lon=lon_ddmm, lon_dir=data[4],
#                                          speed=data[5], direction=data[6], date=date_str, mode='A',                  
#                                          checksum=calculate_checksum(rmc_template.format(time=time_str,              
#                                          lat=lat_ddmm, lat_dir=data[2], lon=lon_ddmm, lon_dir=data[4],               
#                                          speed=data[5], direction=data[6], date=date_str, mode='A', checksum='')))   
        # Если имя выходного файла было указано, сохраняем результат в файл
        if output_filename:
            with open(output_filename, 'w') as f:
                f.write(rmc_message)
        else:
            # Иначе просто выводим результат на экран
            print(rmc_message)
else:
    print_help()
