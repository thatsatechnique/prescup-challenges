from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

def run_async_server():
    software_version = "1.1.9"
    num_registers = 50

    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * num_registers),
        co=ModbusSequentialDataBlock(0, [0] * num_registers),
        hr=ModbusSequentialDataBlock(0, [0, 7, 3, 100]),
        ir=ModbusSequentialDataBlock(0, [9, 6, 150]))

    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName = "Vendor Name=Automated Pool Management"
    identity.ProductCode = "Product Code=PCM v1.1.9"
    identity.VendorUrl = "http://apm.pccc"
    identity.ProductName = "Product Name=Pool Chemical Manager"
    identity.ModelName = "Model Name=PCM v1.1.9"
    identity.MajorMinorRevision = "Software Version=" + software_version
  
    StartTcpServer(context=context, host="0.0.0.0", identity=identity, address=("0.0.0.0", 502))

if __name__ == "__main__":
    print("Modbus server running on port 502")
    run_async_server()


