#! /usr/bin/env python3
import serial
import multiprocessing
import queue
import time

class CNC_move(multiprocessing.Process):
    open = False
    def __init__(self, serial_port):
        self.q1 = multiprocessing.Queue()
        self.q2 = multiprocessing.Queue()
        # self.q1 = multiprocessing.Queue()
        # self.q2 = multiprocessing.Queue()
        super(CNC_move, self).__init__(target=self.goto_iterator,args=(serial_port, self.q1, self.q2))
        self.start()
        self.open = True

    def goto_iterator(self, serial_port, q1, q2):
        # print('Hallo')
        self.cnc = serial.Serial(serial_port, baudrate=115200, timeout=0)

        self.__con_cnc(q2)
        self.__goto(q1,q2)
        self.__discon_cnc()

    def wfd(self, block=True ):
        try:
            message = self.q2.get(block)
        except queue.Empty:
            #print("nothing in Queue")
            return False
        else:
            if message[0] == 'DONE':
                return True
            elif message[0] == 'DONE1':
                # self.close_all()
                self.q2.put(['DONE1']) 
            else:
                print('Error', message[0])
                return None


    #def wfd(self):
    #    while 1:
    #        message = self.q2.get()
    #        if message[0] == 'DONE':
    #            print(message[0])
    #            break

    def move(self, xx, yy):
        self.q1.put([xx,yy])

    def speed(self, speed):
        self.q1.put(['SPEED',speed])


    def fixed_read_line(self):
        line = b''
        while 1:
            line = line + self.cnc.readline()
            # print(line)
            if b'\r\n' in line:
                return line

    def close_all(self):
        self.join()
        self.q1.close()
        self.close()
        self.open = False
        
    def __del__(self):
        # print('closeBefehl')
        if self.open:
            self.q1.put(['STOP'])
            answer = self.q2.get()
            # print(answer)
            if answer[0] == 'DONE1':
                self.close_all()
            else:
                raise Exception("ERROR during waiting for DONE!")
            # self.__discon_cnc()
            # self.cnc.close()
            

    def __con_cnc(self, q2):
        if self.cnc.is_open:
            print("is opened")
            self.cnc.close()
            # self.__del__()
            # self.cnc.close()
        self.cnc.open()
        self.cnc.flush()
        # command = 'T6\r\n'
        # cnc.write(str.encode(command))
        print("wait for connection with CNC...")
        while 1:
            line = self.fixed_read_line()
            # print(line)
            if line == b'start\r\n':
                # print(line)
                q2.put(['DONE'])
                break  
        print("connected with CNC...")
    
    def __discon_cnc(self):
        if self.cnc.is_open:
            self.cnc.close()

    def __goto(self, q1, q2):
        """ Multiprocess CNC movement.

        This function move the CNC-Machine in X and Y. this happens 
        with a Multiprocess and the Positions got by a Query. There
        are two Options to Pass to the Process:
        1: Pass 2 Numbers in a List, the X and Y Value for the CNC. [X,Y]
        2: Pass 'Exit' in a List to close the Process. ['EXIT']

        Args:
            cnc: ComPortObject of the CNC Machine.
            q1:  Query to get the X,Y positions and the STOP Command.
            q2:  Query to send DONE Commands to the Main Process.

        Returns:
            Void

        Examples:
            >>>
            import multiprocessing
            import CNC_move as cnc

            def main():
                q1 = multiprocessing.Queue()
                q2 = multiprocessing.Queue()
                msm = cnc.CNC_move("COM5",q1,q2)
                msm.start()
                q1.put([100,100])
                while 1:
                    message = q2.get()
                    if message[0] == 'DONE':
                        break
                q1.put(['STOP'])
                msm.join()

            if __name__ == '__main__':
                main()
        """
        while 1: 
            message = q1.get()
            # print(message)
            if message[0] == 'STOP':
                q2.put(['DONE1'])
                break
            elif message[0] == 'SPEED':
                # command = 'G19 S'+str(message[1])+'\r\n'
                command = 'T5 S'+str(message[1])+'\r\n'
                self.cnc.write(str.encode(command))
                # q1.join()
                self.cnc.flush()
                while 1:
                    line = self.fixed_read_line()
                    if line == b'done\r\n':
                        q2.put(['DONE'])
                        break
            else:
                # command = 'G1 Y'+str(message[0])+' Z'+str(message[1])+'\r\n'
                # command = 'T1 X'+str(message[0])+' Y'+str(round(message[1]*33.775))+'\r\n'
                command = 'T1 X'+str(message[0])+' Y'+str(round(message[1]))+'\r\n'
                #print(str.encode(command))
                self.cnc.write(str.encode(command))
                # q1.join()
                self.cnc.flush()
                # print(message)

                while 1:
                    line = self.fixed_read_line()
                    if line == b'done\r\n':
                        q2.put(['DONE'])
                        # print(line)
                        break
        print("Completed")
        # q2.put(['DONE'])
        

if __name__ == "__main__":
    msm = CNC_move("COM9")
    # msm = CNC_move("/dev/ttyUSB0")
    msm.wfd(True)
    msm.speed(100)  #the lower the faster
    msm.wfd(True)
    t1 = time.time()
    print("Start >> Forward Rotation")
    msm.move(0, 12159) #180/12159 and 360/24318   i.e 1degree = 67.55
    msm.wfd(True)
    print("Stop") #the first rotation stops
    print("Time to Complete Fwd Rotation : " , time.time() -t1, "seconds") 
    time.sleep(10) #waiting time before totating back to the initial position
    print("Start << Reverse Rotation") 
    msm.move(0,0)
    msm.wfd(True)   
    print("Reverse Rotation Completed")  
    print("Time to Complete Fwd+Delay+Rvrs Rotation : " , time.time() -t1,"seconds") 
    while 1:
        if msm.wfd(False):
            break
        else:
            # print('test')
            pass

    
