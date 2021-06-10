from datetime import datetime


def lambda_handler(event, context):
    now = datetime.utcnow()
    batch_id = now.timestamp()
    targets = [{
        'title': 'Appworks School',
        'address': '110台北市信義區基隆路一段178號',
        'gps': (25.0424488, 121.562731),
        'batch_id': batch_id
    }, {
        'title': '宏大弘資源回收場',
        'address': '105台北市松山區撫遠街409號',
        'gps': (25.0657733, 121.5649126),
        'batch_id': batch_id
    }, {
        'title': '永清工程行',
        'address': '115南港區成福路121巷30號',
        'gps': (25.0424398, 121.5858762),
        'batch_id': batch_id
    }, {
        'title': '7-ELEVEN 惠安門市',
        'address': '110台北市信義區吳興街520號',
        'gps': (25.0221574, 121.5666836),
        'batch_id': batch_id
    }, {
        'title': '路易莎咖啡',
        'address': '106台北市大安區忠孝東路三段217巷4弄2號',
        'gps': (25.0424876, 121.5400285),
        'batch_id': batch_id
    }]
    return {'statusCode': 200, 'data': targets}
