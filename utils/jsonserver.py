
# tile = Tile("MODIS_Terra_Brightness_Temp_Band31_Day", date=date, verbose=True)

# r = {}
# r['meta'] = [{'short_name' : tile.layer, 'time': {'start': 1306886400, 'iso_stop': \
#     '{}T00:00:00+0000'.format(d2.strftime('%Y-%m-%d')), 'iso_start': '{}T00:00:00+0000'.format(d1.strftime('%Y-%m-%d')), \
#         'stop': 1401580800}, 'bounds': {'west': -26.467181536012703, 'east': 0.5631315220428235, 'north': -11.26263044085647, \
#             'south' : -38.85607502095485}}]

# r['data'] = []

# for entry in info:
#     r['data'].append([{'std' : np.sqrt(entry[4]), 'cnt' : 3000, 'iso_time' : \
#         '{}T00:00:00+0000'.format(entry[0]), 'min' : entry[2], 'max' : entry[3], 'time' : 0, 'ds' : 0, 'mean' : entry[1]}])


# r['stats'] = {}

# with open("../app/data.json", "w") as f:
#     f.write(json.dumps(r))

# tiles = get_all_tiles('1km', '2')
# means = np.array([tile.mean() for tile in tiles])
# print(means.mean())
