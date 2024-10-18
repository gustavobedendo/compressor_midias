# -*- coding: utf-8 -*-
"""
Created on Mon Aug  9 14:04:17 2021

@author: gustavo.bedendo
"""
import multiprocessing, getopt, sys, os, subprocess, traceback
import shutil, time, math, signal, time
from PIL import Image
from random import seed
from random import randint
from threading import Timer

import socket, platform
#mport logging

seed(1)
global listimg, listvid, listother

global vidprocs, imgprocs
vidprocs = []
imgprocs = []
listavidformats = [".webm", ".mkv", ".flv", ".flv", ".vob", ".ogv", ".ogg", ".avi",\
            ".mts", ".ts", ".mov", ".qt", ".yuv", ".rm", ".rmvb", ".asf", ".mp4", ".m4p", ".m4v", ".mpg", ".mpeg", ".mpg", ".3gp", ".flv", ".dav"]
listaimgformats = [".jpg", ".jpeg", ".png", ".bmp"]
#listimg = []
#listvid = []
listother = []



class CompressionItem():
    global logsDir
    def __init__(self, arquivoorg = None, arquivosaida=None, tipo="", tamanho=None, rootdir = None):
        self.arquivoorg = arquivoorg
        self.arquivosaida = arquivosaida
        basename = os.path.basename(arquivoorg)
        self.tempdir = os.path.join(rootdir, "tempComp")
        self.arquivomid = os.path.join(self.tempdir, str(randint(0, 100))+basename+".mp4")
        self.arquivosaida = arquivosaida
        self.tipo = tipo
        self.rootdir = rootdir
        self.tamanho = tamanho
        self.logfile = os.path.join(logsDir, "logs-{}".format(tipo), basename+".txt")
        
        
def validateJpeg():
    folder = r"R:\testejpeg"
    for file in os.listdir(folder): 
        with open(os.path.join(folder,file), 'rb') as filejpg:
            machinestate = 0
            filejpg.seek(0, 2)
            file_size = filejpg.tell()
            filejpg.seek(0, 0) 
            #0 = start
            #1 after start before ffda (SOC) 
            #2 after SOC, looking form ffd9
            #print(file)
            cont = 1
            start = 0
            #bytesimg = b''
            while(True):
                if(machinestate==0):
                    print(filejpg.tell())
                    first2bytes = filejpg.read(2)
                    if(first2bytes==b'\xff\xd8'):
                        machinestate = 1
                        marker = filejpg.read(2)
                    else:
                        print(filejpg.tell())
                        print("ERROR", first2bytes)
                        break
                elif(machinestate==1):
                    length_chunk_bytes = filejpg.read(2)
                    length_chunk = int.from_bytes(length_chunk_bytes, byteorder='big')
                    chunk = filejpg.read(length_chunk)
                    if(chunk[-2:]==b'\xff\xda'):
                        machinestate = 2
                        #break
                elif(machinestate==2):
                    current_pointer = filejpg.tell()
                    lastbytes = filejpg.read()
                    nextffd9 = lastbytes.find(b'\xff\xd9')
                    if(nextffd9!=-1):                          
                        if(current_pointer+nextffd9+2==file_size):                            
                            print("{} - JPEG COM FFD9 NO FINAL".format(file))
                            break
                        else:
                            filejpg.seek(start, 0)
                            print('0', current_pointer+nextffd9+2)
                            bytesreaduntilffd9 =  filejpg.read(current_pointer+nextffd9+2)
                            with open(os.path.join(folder,"temp-{}-".format(cont)+file), 'wb') as filejpgtemp:
                                filejpgtemp.write(bytesreaduntilffd9)
                            print("{} - JPEG COM CARONA".format(file))
                            cont += 1
                            #filejpg.seek(current_pointer+nextffd9+2, 0)
                            lastbytes = filejpg.read()
                            nextffd8 = lastbytes.find(b'\xff\xd8')
                            print('1', filejpg.tell(), nextffd8)
                            start = current_pointer+nextffd9+2+nextffd8
                            filejpg.seek( current_pointer+nextffd9+2+nextffd8, 0)
                            print('2', filejpg.tell())
                            machinestate = 0
                    else:
                        print("{} - JPEG CORROMPIDO".format(file))
                        break
                    #break
                    


def recursiveDir(rootdir, diretorioorg, diretoriocomp, basename=None, tarfile=None, arquivos = ""):
    global imgsizemin, vidsizemin, sizeimgorg, sizeimgnew, sizevidorg, sizevidnew, sizeglobalorg, sizeglobalnew, validarjpeg, compvideos, compimagens
    #print(rootdir, diretorioorg, diretoriocomp)
    for file in os.listdir(diretorioorg):
        if(os.path.isdir(os.path.join(diretorioorg, file))):
           
            #print(rootdir, diretorioorg, diretoriocomp, file)
            arquivos = recursiveDir(rootdir, os.path.join(diretorioorg, file), os.path.join(diretoriocomp, file), basename=basename, tarfile=tarfile, arquivos=arquivos)
        else:
            filename, extension = os.path.splitext(file)
            #print(file)
            filesizeorg = int(os.path.getsize(os.path.join(diretorioorg, file))/1024)
            if(compvideos and extension.lower() in listavidformats):
               
                if(filesizeorg>=vidsizemin):
                    if(tarfile==None):
                        ci = CompressionItem(arquivoorg = os.path.join(diretorioorg, file), arquivosaida=os.path.join(diretoriocomp, os.path.basename(file)), tipo="video", rootdir=rootdir)
                        listvid.append(ci)
                    else:
                        if(len(arquivos) >= 1000):
                        #print("tar -rvf {} -C \"{}\" \"{}\" ".format(tarfile, basename, relpath))
                            subprocess.run("tar -rf {} -C \"{}\" {}".format(tarfile, basename, arquivos), check=True)
                            arquivos = ""
                        relpath = "../other_partition_used_to_compress/"
                        try:
                            relpath = os.path.relpath(os.path.join(diretorioorg, file), start=basename)
                        except:
                            None
                        arquivos +=  " \"{}\"".format(relpath)
                        
                        
                else:
                    sizeglobalorg.value += filesizeorg
                    sizeglobalnew.value += filesizeorg
                    ci = CompressionItem(arquivoorg = os.path.join(diretorioorg, file), arquivosaida=os.path.join(diretoriocomp, os.path.basename(file)), rootdir=diretorioorg)
                    listother.append(ci)
                    #if(not os.path.isdir(os.path.dirname(os.path.join(diretoriocomp, os.path.basename(file))))):
                    #    os.makedirs(os.path.dirname(os.path.join(diretoriocomp, os.path.basename(file))))
                    #shutil.copyfile(os.path.join(diretorioorg, file), os.path.join(diretoriocomp, os.path.basename(file)))
                    #sizevidorg.value += filesizeorg
                    #sizevidnew.value += filesizeorg
            elif(compimagens and extension.lower() in listaimgformats):
                filesizeorg = int(os.path.getsize(os.path.join(diretorioorg, file))/1024)
                if(filesizeorg<imgsizemin):
                    sizeglobalorg.value += filesizeorg
                    sizeglobalnew.value += filesizeorg
                    ci = CompressionItem(arquivoorg = os.path.join(diretorioorg, file), arquivosaida=os.path.join(diretoriocomp, os.path.basename(file)), rootdir=diretorioorg)
                    listother.append(ci)
                elif(validarjpeg and ("jpeg" in extension.lower() or "jpg" in extension.lower())):
                    find_str = "ERROR"
                    with open(os.path.join(diretorioorg, file), 'rb') as filejpg:
                        filejpg.seek(-1024, os.SEEK_END)  # Note minus sign
                        ultimos1024bytes = filejpg.read()
                        #print(ultimos1024bytes)
                        if(b'\xff\xd9' in ultimos1024bytes):
                            if(tarfile==None):
                                ci = CompressionItem(arquivoorg = os.path.join(diretorioorg, file), arquivosaida=os.path.join(diretoriocomp, os.path.basename(file)), tipo="imagem", rootdir=rootdir)
                                listimg.append(ci)
                            else:
                                if(len(arquivos) >= 1000):
                                #print("tar -rvf {} -C \"{}\" \"{}\" ".format(tarfile, basename, relpath))
                                    subprocess.run("tar -rf {} -C \"{}\" {}".format(tarfile, basename, arquivos), check=True)
                                    arquivos = ""
                                relpath = "../other_partition_used_to_compress/"
                                try:
                                    relpath = os.path.relpath(os.path.join(diretorioorg, file), start=basename)
                                except:
                                    None
                                arquivos +=  " \"{}\"".format(relpath)
                            
                        else:
                            sizeglobalorg.value += filesizeorg
                            sizeglobalnew.value += filesizeorg
                            ci = CompressionItem(arquivoorg = os.path.join(diretorioorg, file), arquivosaida=os.path.join(diretoriocomp, os.path.basename(file)), rootdir=diretorioorg)
                            #print(os.path.join(diretorioorg, file))
                            listother.append(ci)
                elif(filesizeorg>=imgsizemin):
                    if(tarfile==None):
                        ci = CompressionItem(arquivoorg = os.path.join(diretorioorg, file), arquivosaida=os.path.join(diretoriocomp, os.path.basename(file)), tipo="imagem", rootdir=rootdir)
                        listimg.append(ci)
                    else:
                        if(len(arquivos) >= 1000):
                        #print("tar -rvf {} -C \"{}\" \"{}\" ".format(tarfile, basename, relpath))
                            subprocess.run("tar -rf {} -C \"{}\" {}".format(tarfile, basename, arquivos), check=True)
                            arquivos = ""
                        relpath = "../other_partition_used_to_compress/"
                        try:
                            relpath = os.path.relpath(os.path.join(diretorioorg, file), start=basename)
                        except:
                            None
                        arquivos +=  " \"{}\"".format(relpath)
                        #print("tar -rvf {} -C \"{}\" \"{}\" ".format(tarfile, basename, relpath))
                        #subprocess.run("tar -rf {} -C \"{}\" \"{}\"".format(tarfile, basename, relpath), check=True)
                else:
                    sizeglobalorg.value += filesizeorg
                    sizeglobalnew.value += filesizeorg
                    ci = CompressionItem(arquivoorg = os.path.join(diretorioorg, file), arquivosaida=os.path.join(diretoriocomp, os.path.basename(file)), rootdir=diretorioorg)
                    listother.append(ci)
                    #if(not os.path.isdir(os.path.dirname(os.path.join(diretoriocomp, os.path.basename(file))))):
                    #    os.makedirs(os.path.dirname(os.path.join(diretoriocomp, os.path.basename(file))))
                    #shutil.copyfile(os.path.join(diretorioorg, file), os.path.join(diretoriocomp, os.path.basename(file)))
                    #sizeimgorg.value += filesizeorg
                    #sizeimgnew.value += filesizeorg
            else:
               sizeglobalorg.value += filesizeorg
               sizeglobalnew.value += filesizeorg
               ci = CompressionItem(arquivoorg = os.path.join(diretorioorg, file), arquivosaida=os.path.join(diretoriocomp, os.path.basename(file)), rootdir=diretorioorg)
               #print(os.path.join(diretorioorg, file))
               listother.append(ci)
        #else:
    return arquivos        
            


def iterateOverDirs(tarfile=None, diretoriosaida=None):
    global dirs, override, logsDir, isclient
    if(override and not isclient):
        try:
            shutil.rmtree(logsDir)
        except:
            None
            
    for diretorio in dirs:
        if(override and not isclient):
            print("Deletando ", os.path.join(os.path.dirname(diretorio), diretorio+"-compressed"))
            try:
                shutil.rmtree(os.path.join(os.path.dirname(diretorio), diretorio+"-compressed"))
            except:
                None
            try:
                shutil.rmtree(os.path.join(diretoriosaida, os.path.basename(diretorio)+"-compressed)"))
            except:
                None
        #print(diretorio)
        print("Examinando {} ".format(os.path.join(os.path.dirname(diretorio), diretorio)))
        diretoriosaida_inner = diretorio
        if(diretoriosaida!=None):
            diretoriosaida_inner = os.path.join(diretoriosaida, os.path.basename(diretorio))
        arquivos = recursiveDir(os.path.dirname(diretorio), diretorio, diretoriosaida_inner+"-compressed", basename=os.path.dirname(diretorio), tarfile=tarfile)
        if(tarfile!=None):
            subprocess.run("tar -rf \"{}\" -C \"{}\" {}".format(tarfile, os.path.dirname(diretorio), arquivos), check=True)


def NConvertProcess(listimg, qimg, maxdim, indeximg, sizeimgorg, sizeimgnew, sizeglobalorg, sizeglobalnew, listaprocesssos, idp, erros, keepfixed, all_status_img): 
    index = -1
    with indeximg.get_lock():
        index = indeximg.value
        indeximg.value += 1

    while(index < len(listimg) and index!=-1):
        compimg = listimg[index]
        abs_file_input = compimg.arquivoorg
        abs_file_mid = compimg.arquivomid
        abs_file_output = compimg.arquivosaida
        abs_root_dir = compimg.rootdir
        #print(abs_root_dir, abs_file_input)
        relative_input = abs_file_input
        relative_output = abs_file_output
        relative_mid = abs_file_mid
        try:
            relative_input = os.path.relpath(abs_file_input, abs_root_dir)
            relative_output = os.path.relpath(abs_file_output, abs_root_dir)
            relative_mid = os.path.relpath(abs_file_mid, abs_root_dir)
        except:
            None
        logfile = compimg.logfile
        if(not os.path.isdir(os.path.dirname(abs_file_output))):
            try:
                os.makedirs(os.path.dirname(abs_file_output))
            except:
                None
        if(not os.path.isdir(os.path.dirname(abs_file_mid))):
            try:
                os.makedirs(os.path.dirname(abs_file_mid))
            except:
                None
        if(not os.path.isdir(os.path.dirname(logfile))):
            try:
                os.makedirs(os.path.dirname(logfile))
            except:
                None
        try:
            try: 
                if(not os.path.exists(abs_file_output)):
                    #continue
                    application_path = ""
                    if getattr(sys, 'frozen', False):
                        # If the application is run as a bundle, the PyInstaller bootloader
                        # extends the sys module by a flag frozen=True and sets the app 
                        # path into variable _MEIPASS'.
                        application_path = sys._MEIPASS
                    else:
                        application_path = os.path.dirname(os.path.abspath(__file__))
                    nconvertpath = os.path.join(application_path, 'nconvert.exe')
                    image = Image.open(abs_file_input)    
                    width, height = image.size
                    if(height>=2048 or width>=2048):
                        ratio1 = round(min((1024/width)*(100),(1024/height)*(100)))
                        
                        if(height > width):
                            compcmd =  "\"{}\" -overwrite -ratio -rtype lanczos -resize  {}% {}% -q {} -clevel 9 -c 1 -no_auto_ext -o \"{}\" \"{}\""
                        else:
                            compcmd = "\"{}\" -overwrite -ratio -rtype lanczos -resize {}% {}% -q {} -clevel 9 -c 1 -no_auto_ext -o \"{}\" \"{}\""
                        cmd = compcmd.format(nconvertpath, ratio1, ratio1, qimg, abs_file_mid, relative_input)
                        #print(cmd)
                        popen = subprocess.Popen(cmd, cwd = abs_root_dir,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        '''
                        with open(logfile, encoding='utf-8', mode='w') as arquivo:
                        while True:
                            try:
                                line = popen.stdout.readline()
                                if not line:
                                    break
                            
                                try:                
                                    if ("Input" in line and ", from" in line and False):
                                        None
                                    elif "Output" in line and ", to " in line:
                                        split = line.split(", to ")
                                        arquivo.write(split[0]);
                                        arquivo.write(", to ");
                                        arquivo.write("~\'" + relative_output + "\'\n");
                                    else:
                                        arquivo.write(line);
                                    
                                except:
                                    exc_type, exc_value, exc_tb = sys.exc_info()
                                    erros.append(traceback.format_exception(exc_type, exc_value, exc_tb))
                            except UnicodeDecodeError:
                                None
                        '''
                        return_code = popen.wait()
                        #print(return_code)
                        if(return_code==0):
                            #print("OK:", abs_file_input, abs_file_output,return_code)
                            try:
                                shutil.move(abs_file_mid, abs_file_output)
                                all_status_img[os.path.basename(abs_file_output)] = "Comprimido"
                                #os.rename(abs_file_mid, abs_file_output)
                            except:
                                #traceback.print_exc()
                                shutil.copyfile(abs_file_input, abs_file_output)    
                                all_status_img[os.path.basename(abs_file_output)] = "Copiado"
                                try:                                               
                                    os.remove(abs_file_mid)
                                except:
                                    None
                                    #exc_type, exc_value, exc_tb = sys.exc_info()
                                    #erros.append(traceback.format_exception(exc_type, exc_value, exc_tb))
                        else:
                            #print("Erro:", abs_file_input, abs_file_output,return_code)
                            shutil.copyfile(abs_file_input, abs_file_output)
                            all_status_img[os.path.basename(abs_file_output)] = "Copiado"
                            try:
                                os.remove(abs_file_mid)
                            except:
                                None
                    else:
                        #print("Erro:", abs_file_input, abs_file_output,return_code)
                        shutil.copyfile(abs_file_input, abs_file_output)
                        all_status_img[os.path.basename(abs_file_output)] = "Copiado"
                        try:
                            os.remove(abs_file_mid)
                        except:
                            None
                
            except:   
                #traceback.print_exc()
                shutil.copyfile(abs_file_input, abs_file_output)
                all_status_img[os.path.basename(abs_file_output)] = "Copiado"
            finally:
                try:
                    popen.terminate()
                except:
                    None
        except:
            all_status_img[os.path.basename(abs_file_output)] = "ERRO"
            #print("Erro:", abs_file_input, abs_file_output)
        try:
            os.utime(abs_file_output, (os.path.getatime(abs_file_input), os.path.getmtime(abs_file_input)))
        except:
            None
        with indeximg.get_lock():
            with sizeglobalorg.get_lock():
                
                filesizeorg = os.path.getsize(abs_file_input)
                filesizenew = os.path.getsize(abs_file_output)
                #sizeglobalorg = 
                sizeglobalorg.value += int(filesizeorg/1024)
                sizeglobalnew.value += int(filesizenew/1024)
                sizeimgorg.value += int(filesizeorg/1024)
                sizeimgnew.value += int(filesizenew/1024)
                index = indeximg.value
                if(index>=len(listimg)):
                    return
                indeximg.value += 1


def FFMpegProcess(listvid, qvid, indexvid, sizevidorg, sizevidnew, sizeglobalorg, sizeglobalnew, listaprocesssos, idp, erros, keepfixed, all_status_vid, debug=False, cuda=False):
    application_path = ""
    highcomp = "\"{}\" {} -nostdin -y -i \"{}\" -filter:v scale='w=if(gt(ih\\,iw)\\,-2\\,480):h=if(gt(ih\\,iw)\\,480\\,-2)' -r 20"\
                    + " -vcodec libx265 -crf 32  -acodec aac -ar 22050 -ab 48k -ac 1 -map_metadata 0 "\
                    + "-movflags use_metadata_tags  \"{}\""
    lowcomp = "\"{}\" {} -nostdin -y -i \"{}\" -vcodec libx265 -crf 32  -acodec aac -ar 22050 -ab 48k -ac 1 -map_metadata 0  -movflags use_metadata_tags \"{}\""

    index = -1
    with indexvid.get_lock():
        index = indexvid.value
        indexvid.value += 1
    while(index < len(listvid) and index!=-1):
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        ffmpegpath = os.path.join(application_path, 'ffmpeg.exe')
        use_cuda = ""
        if(cuda):
            use_cuda = "-hwaccel cuda" 
        if(platform.system()=="Linux"):
            ffmpegpath = 'ffmpeg'
            use_cuda = ""
        compcmd = highcomp
        if(qvid <= 0):
            compcmd = lowcomp
        compvid = listvid[index]
        abs_file_input = compvid.arquivoorg
        abs_file_mid = compvid.arquivomid
        abs_file_output = compvid.arquivosaida
        
        abs_root_dir = compvid.rootdir
        #print(abs_root_dir, abs_file_input)
        relative_input = abs_file_input
        relative_output = abs_file_output
        relative_mid = abs_file_mid
        try:
            relative_input = "./"+os.path.relpath(abs_file_input, abs_root_dir)
            relative_output = "./"+os.path.relpath(abs_file_output, abs_root_dir)
            relative_mid = "./"+os.path.relpath(abs_file_mid, abs_root_dir)
        except:
            None
        
        logfile = compvid.logfile
        #check for dirs
        if(not os.path.isdir(os.path.dirname(abs_file_output))):
            try:
                os.makedirs(os.path.dirname(abs_file_output))
            except:
                None
        if(not os.path.isdir(os.path.dirname(abs_file_mid))):
            try:
                os.makedirs(os.path.dirname(abs_file_mid))
            except:
                None
        if(not os.path.isdir(os.path.dirname(logfile))):
            try:
                os.makedirs(os.path.dirname(logfile))
            except:
                None
        
            #continue
        cmd = compcmd.format(ffmpegpath, use_cuda, relative_input, relative_mid)
        #print(cmd)
        try:
        #print(cmd)
            with open(logfile, encoding='utf-8', mode='w') as arquivo:
                try:
                    if(debug):
                        arquivo.write(f"Using cuda: {cuda}\n")
                        arquivo.write(cmd+"\n")
                    if(not os.path.exists(abs_file_output)):
                        temp_size = math.ceil(os.path.getsize(abs_file_input) / (1024*1024))
                        n_lines = 0
                        kill = lambda process: process.kill()

                        timeout_size_based = temp_size * 120
                        popen = subprocess.Popen(cmd, cwd = abs_root_dir,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)#universal_newlines=True)
                        my_timer = Timer(timeout_size_based, kill, [popen])
                        try:
                            my_timer.start()
                            #stdout, stderr = popen.communicate()
                            
                                
                            while True:
                                
                                line = popen.stdout.readline().decode('utf-8', errors="ignore")
                                if not line: break
                                try:                
                                    if ("Input" in line and ", from" in line and False):
                                        None
                                    elif "Output" in line and ", to " in line:
                                        split = line.split(", to ")
                                        arquivo.write(split[0])
                                        arquivo.write(", to ")
                                        arquivo.write("~\'" + relative_output + "\'")
                                    else:
                                        arquivo.write(line)
                                    
                                except:
                                    None
                        except:
                            traceback.print_exc()
                            time.sleep(2)
                        finally:
                            my_timer.cancel()
                            
                                        #exc_type, exc_value, exc_tb = sys.exc_info()
                                        #erros.append(traceback.format_exception(exc_type, exc_value, exc_tb))
                            
                        return_code = popen.wait()
                        arquivo.write(f"Return code: {return_code}")
                        #print()
                        #print(relative_input, return_code)
                        if(return_code==0):
                            try:
                                shutil.move(abs_file_mid, abs_file_output)
                                #os.rename(abs_file_mid, abs_file_output)
                                all_status_vid[os.path.basename(abs_file_output)] = "Comprimido"
                            except:
                                #traceback.print_exc()
                                try:
                                    None
                                    
                                    shutil.copyfile(abs_file_input, abs_file_output)
                                    all_status_vid[os.path.basename(abs_file_output)] = "Copiado"
                                    os.remove(abs_file_mid)
                                    
                                except:
                                    traceback.print_exc()
                                    exc_type, exc_value, exc_tb = sys.exc_info()
                                    erros.append(traceback.format_exception(exc_type, exc_value, exc_tb))
                        else:
                            if(keepfixed):                            
                                if(os.path.exists(abs_file_mid) and os.path.getsize(abs_file_mid) > 0):
                                    shutil.move(abs_file_mid, abs_file_output)
                                    #os.rename(abs_file_mid, abs_file_output)
                                    all_status_vid[os.path.basename(abs_file_output)] = "Comprimido"
                                else:
                                    shutil.copyfile(abs_file_input, abs_file_output)
                            else:
                        
                                shutil.copyfile(abs_file_input, abs_file_output)
                                all_status_vid[os.path.basename(abs_file_output)] = "Copiado"
                                try:
                                    os.remove(abs_file_mid)
                                except:
                                    None
                                #traceback.print_exc()
                                #exc_type, exc_value, exc_tb = sys.exc_info()
                                #erros.append(traceback.format_exception(exc_type, exc_value, exc_tb))
                        
                except:
                    if(debug):
                        arquivo.write(traceback.format_exc())
                    #traceback.print_exc()
                    
                    shutil.copyfile(abs_file_input, abs_file_output)
                    all_status_vid[os.path.basename(abs_file_output)] = "Copiado"
                    
                finally:
                    try:
                        popen.terminate()
                    except:
                        None
        except:
            all_status_vid[os.path.basename(abs_file_output)] = "ERRO"
            #print("Erro:", abs_file_input, abs_file_output)
        try:
            os.utime(abs_file_output, (os.path.getatime(abs_file_input), os.path.getmtime(abs_file_input)))
        except:
            None
        with indexvid.get_lock():
             with sizeglobalorg.get_lock():
                filesizeorg = os.path.getsize(abs_file_input)
                filesizenew = os.path.getsize(abs_file_output)
                
                #sizeglobalorg = 
                sizeglobalorg.value += int(filesizeorg/1024)
                sizeglobalnew.value += int(filesizenew/1024)
                sizevidorg.value += int(filesizeorg/1024)
                sizevidnew.value += int(filesizenew/1024)
                
                index = indexvid.value
                if(index>=len(listvid)):
                    return
                indexvid.value += 1
            
            
def ProcessoPrintador(listimg, listvid, indeximg, indexvid, sizeimgorg, sizeimgnew, sizevidorg, sizevidnew, sizeglobalorg, sizeglobalnew, verbose=0, client_socket=None):
    
    while(True):
        try:
            with sizeimgnew.get_lock():
                taxacompressaoimg = round(sizeimgnew.value / sizeimgorg.value, 2)*100
            with sizevidnew.get_lock():
                taxacompressaovid = round(sizevidnew.value / sizevidorg.value, 2)*100
            with sizeglobalorg.get_lock():
                taxacompressaoglobal = round(sizeglobalnew.value / sizeglobalorg.value, 2)*100
            
            imprimir = "Comprimindo: Imagens {} / {} Taxa compressao: {:<4.2f}% - Vídeos {} / {} Taxa compressao:  {:<4.2f}%  --- Compressão global: {:<4.2f}%".format\
                  (min(indeximg.value, len(listimg)), len(listimg), taxacompressaoimg, min(indexvid.value,len(listvid)), len(listvid), taxacompressaovid, taxacompressaoglobal)
            print("{:150s}".format(imprimir), end="\r")
            if(client_socket!=None):
                client_socket.sendall("{:150s}<ENDING>".format(imprimir).encode())
            
            if(verbose>0):
                print()
                sys.stdout.flush()
            time.sleep(verbose)
        except:
            None
        time.sleep(2)
    
def copyOtherFiles(verbose=0):
    global listother
    count = 0
    print("\n")
    for other in listother:
        try:
            abs_file_input = other.arquivoorg
            abs_file_output = other.arquivosaida
            if(not os.path.isdir(os.path.dirname(abs_file_output))):
                os.makedirs(os.path.dirname(abs_file_output))
            
            shutil.copyfile(abs_file_input, abs_file_output)
            count += 1
            if(verbose>0):
                if(count%200!=1):
                    continue
                else:
                    print()
                    sys.stdout.flush()
            print("Copiando demais arquivos {} / {}".format(count, len(listother)), end="\r")
            
        except:
            traceback.print_exc()

def launchProcesses(client_socket=None, verbose=0):
    global dirs, proci, procv, qimg, imgsizemin, vidsizemin, maxdim, qvid, compvid, compimg, listimg, listvid, listaprocesssos, sizevidorg, sizevidnew, erros, sizeglobalorg, sizeglobalnew
    processes_img = [None] * proci
    processes_vid = [None] * procv
    lockimg = multiprocessing.Lock()
    lockvid = multiprocessing.Lock()
    indeximg = multiprocessing.Value('i', 0)
    indexvid = multiprocessing.Value('i', 0)
    idp = 0
    print(f"Will use cuda: {cuda}")
    print(f"Is Debug Mode: {debug}")
    for pimg in range(proci):
        processes_img[pimg] = multiprocessing.Process(target=NConvertProcess, args=(listimg, qimg, maxdim,\
                                                                                    indeximg, sizeimgorg, sizeimgnew, sizeglobalorg, sizeglobalnew, listaprocesssos, idp, erros, keepfixed, all_status_img,), daemon=True)   
        listaprocesssos.append(None)
        processes_img[pimg].start()
        idp +=1
        
    for pvid in range(procv):
        processes_vid[pvid] = multiprocessing.Process(target=FFMpegProcess, args=(listvid, qvid, \
                                                                                  indexvid, sizevidorg, sizevidnew, sizeglobalorg, sizeglobalnew, listaprocesssos, idp, erros, keepfixed, all_status_vid, debug, cuda,), daemon=True)
        listaprocesssos.append(None)
        processes_vid[pvid].start()
        idp += 1
        
    printer = multiprocessing.Process(target=ProcessoPrintador, args=(listimg, listvid, indeximg, indexvid, sizeimgorg, sizeimgnew, sizevidorg, sizevidnew, sizeglobalorg, sizeglobalnew, verbose, client_socket,), daemon=True)
    printer.start()
    for pimg in processes_img:
        pimg.join()
    for pvid in processes_vid:
        pvid.join()
    printer.terminate() 
    
def recursiveDirValidate(diretorioorg, diretoriocomp, validado):
    for file in os.listdir(diretorioorg):
        if(os.path.isdir(os.path.join(diretorioorg, file))):
            validado = recursiveDirValidate(os.path.join(diretorioorg, file), os.path.join(diretoriocomp, file), validado)            
        else:           
            arquivosaida=os.path.join(diretoriocomp, os.path.basename(file))
            if(not os.path.isfile(arquivosaida)):
                try:
                    shutil.copyfile(os.path.join(diretorioorg, file), arquivosaida)
                except:
                    print(os.path.join(diretorioorg, file), arquivosaida)
                    validado = False         
    return validado

def go():
    global dirs, proci, procv, qimg, imgsizemin, vidsizemin, maxdim, qvid, compvid, compimg, all_status_vid, all_status_img, \
        indeximg, indexvid, sizeimgorg, sizeimgnew, sizevidorg, sizevidnew, listimg, listvid, keepfixed, debug, cuda
    global lockimg, lockvid, erros, listaprocesssos, override, logsDir, isclient, isserver, sizeglobalorg, sizeglobalnew, validarjpeg, compvideos, compimagens
    dirs = []
    proci = 10
    procv = 8
    qimg = 50
    imgsizemin = 40
    vidsizemin = 1024
    maxdim = 1024
    qvid = 1
    argumentList = sys.argv[1:]
    compvideos = True
    compimagens = True
    keepfixed = False
    long_options = ["verbose=", "dir=", "proci=", "procv=", "qimg=", "qvid=", "qvid=", "imgsizemin=", "vidsizemin=", "compvid=", \
                    "compimg=", "maxdim=", "override", "server=", "client=", "naovalidarjpeg", "keepfixed", "yes", "outputdir=", "debug", "cuda"]
    arguments, values = getopt.getopt(argumentList, [], long_options)
    sizeimgorg = multiprocessing.Value('i', 1)
    sizeimgnew = multiprocessing.Value('i', 1)
    sizevidorg = multiprocessing.Value('i', 1)
    sizevidnew = multiprocessing.Value('i', 1)
    sizeglobalorg = multiprocessing.Value('i', 1)
    sizeglobalnew = multiprocessing.Value('i', 1)
    manager = multiprocessing.Manager()
    all_status_img = manager.dict()
    all_status_vid = manager.dict()
    erros = manager.list([])
    listimg = manager.list([])
    listvid = manager.list([])
    listaprocesssos = manager.list([])
    override = False
    isserver = False
    isclient = False
    noconfirm = False
    validarjpeg = True
    noconfirm = False
    outputdir = None
    verbose = 0
    status = 1
    debug = False
    cuda = False
    try:
        for currentArgument, currentValue in arguments:
            if currentArgument in ("--proci"):
                proci = int(currentValue)
            elif currentArgument in ("--cuda"):
                cuda = True
            elif currentArgument in ("--debug"):
                debug = True
            elif currentArgument in ("--outputdir"):
                outputdir = currentValue
            elif currentArgument in ("--verbose"):
                verbose = int(currentValue)
            elif currentArgument in ("--procv"):
                procv = int(currentValue)
            elif currentArgument in ("--qimg"):
                qimg = int(currentValue)
            elif currentArgument in ("--qvid"):
                qvid = int(currentValue)
            elif currentArgument in ("--imgsizemin"):
                imgsizemin = int(currentValue)
            elif currentArgument in ("--vidsizemin"):
                vidsizemin = int(currentValue)
            elif currentArgument in ("--compvid"):
                compvideos = bool(str(currentValue).lower()=='true')
            elif currentArgument in ("--compimg"):
                compimagens = bool(str(currentValue).lower()=='true')
            elif currentArgument in ("--keepfixed"):
                keepfixed = True
            elif currentArgument in ("--maxdim"):
                maxdim = int(currentValue)
            elif currentArgument in ("--dir"):
                try:
                    if(os.path.isdir(os.path.abspath(currentValue))):
                        dirs.append(os.path.abspath(currentValue))
                    else:
                        raise Exception()
                except:
                    print(f"Folder {os.path.abspath(currentValue)} not found!")
            elif currentArgument in ("--override"):
                override = True
            elif currentArgument in ("--naovalidarjpeg"):
                validarjpeg = False
            elif currentArgument in ("--server") and not isclient:
                outputdir = None
                isserver = True
                port = int(currentValue)
            elif currentArgument in ("--yes") or currentArgument in ("--autoconnect"):
                noconfirm = True
            elif currentArgument in ("--client") and not isserver:
                outputdir = None
                isclient = True
                try:
                    currentValue = currentValue.split(":")
                    ipserver = currentValue[0]
                    port = int(currentValue[1])
                except:
                    #return
                    ipserver = ""
                    #port = 8003
            else:
                print("Argumentos: [--proci numero (10)] [--procv numero (8)] [--qimg numero(50)] [--qvid 1 ou 0 (1)]"+
                      " [--imgsizemin numero (40)] [--vidsizemin numero (1024)] [--compvid True ou False (True)] [--compimg True ou False (True)]"+\
                      " [--maxdim numero (1024)] [--override] [--client=[IP:PORTA/EM_BRANCO]] [--naovalidarjpeg] --dir <diretorio> [--dir <diretorio>]"+\
                      " [--keepfixed]")
                return
    except:
        print("Argumentos: [--proci numero (10)] [--procv numero (8)] [--qimg numero(50)] [--qvid 1 ou 0 (1)]"+
              " [--imgsizemin numero (40)] [--vidsizemin numero (1024)] [--compvid True ou False (True)] [--compimg True ou False (True)]"+\
              " [--maxdim numero (1024)] [--override] [--client=[IP:PORTA/EM_BRANCO]] [--naovalidarjpeg] --dir <diretorio> [--dir <diretorio>]"+\
              " [--keepfixed]")
        return
    if(not isserver and len(dirs)==0):
        print("Argumentos: [--proci numero (10)] [--procv numero (8)] [--qimg numero(50)] [--qvid 1 ou 0 (1)]"+
              " [--imgsizemin numero (40)] [--vidsizemin numero (1024)] [--compvid True ou False (True)] [--compimg True ou False (True)]"+\
              " [--maxdim numero (1024)] [--override] [--client=[IP:PORTA/EM_BRANCO]] [--naovalidarjpeg] --dir <diretorio> [--dir <diretorio>]"+\
              " [--keepfixed]")
        return        
    try: 
        SEPARATOR = "<SEPARATOR>"
        BUFFER_SIZE = 4096
        if(isclient):
            #print(ipserver, port)
            apagar = []
            try:
                
                #print("h"+hostteste+"g")
                listadisponiveis = []
                if(ipserver==""):
                    #print("h"+hostteste+"g")
                    ports = [8010]
                    for net in ("10","20"):
                        for i in range(33, 34):
                            for p in ports:
                                #print(p)
                                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                try:
                                    ipserver = "192.168.{}.{}".format(net, i)
                                    
                                    sock.settimeout(0.5)
                                    result = sock.connect_ex((ipserver,p))
                                    if result == 0:
                                        sock.sendall("PROBINGCOMP<ENDING>".encode())
                                        bytes_read = b""
                                        while True:
                                            bytes_read += sock.recv(BUFFER_SIZE)
                                            if(bytes_read==b'AVAILABLECOMP<ENDING>'):
                                                cansend = True
                                                listadisponiveis.append((ipserver, p))
                                                break
                                            elif not bytes_read:
                                                # file transmitting is done
                                                break
                                       
                                        
                                        print("{}:{} Disponível".format(ipserver, p))
                                        break
                                    else:
                                        print("{}:{} Não disponível".format(ipserver, p))
                                except:
                                    traceback.print_exc()
                                finally:
                                    try:
                                        sock.shutdown(socket.SHUT_RDWR)
                                        sock.close()
                                    except:
                                        None
                                    
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:                
                        sock.settimeout(0.5)
                        result = sock.connect_ex((ipserver,port))
                        if result == 0:
                            #listadisponiveis.append((ipserver, port))
                            sock.sendall("PROBINGCOMP<ENDING>".encode())
                            bytes_read = b""
                            while True:
                                bytes_read += sock.recv(BUFFER_SIZE)
                                if(b"<ENDING>" in bytes_read):
                                    if(bytes_read==b'AVAILABLECOMP<ENDING>'):
                                        listadisponiveis.append((ipserver, ipserver))
                                        print("{}:{} Disponível".format(ipserver, port))
                                    break
                                elif not bytes_read:
                                    # file transmitting is done
                                    break
                                
                            print("{} Disponível".format((ipserver)))
                        else:
                            print("{} Não disponível".format(ipserver))
                            
                    except:
                            traceback.print_exc()
                    finally:
                        try:
                            sock.shutdown(socket.SHUT_RDWR)
                            sock.close()
                        except:
                            None
                print("OPÇÕES:")
                print("0 - Sair")
                for i in range(len(listadisponiveis)):
                    print("{} - {}".format(i+1, listadisponiveis[i]))
                opcao = -1
                while True:
                    try:
                        if(noconfirm):
                            if(len(listadisponiveis)==0):
                                return
                            opcao = 1
                            break
                        else:
                            opcao = int(input("Digite a opção do host (ex.: 1): "))
                    except ValueError:
                        print("Opção inválida\n\n\n\n")
                        for i in range(len(listadisponiveis)):
                            print("{} - {}".format(i+1, listadisponiveis[i]))
                        #better try again... Return to the start of the loop
                        continue
                    else:
                        break
                
                opcao = 0
                logsDir = os.path.join(os.path.dirname(os.path.dirname(dirs[0])), "sources", "logsCompressao")
                if(True or opcao > 0):   
                    host = listadisponiveis[opcao-1][0]
                    port = int(listadisponiveis[opcao-1][1])
                    #print(f"[+] Connecting to {host}:{port}")
                    with  socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        print(f"[+] Connecting to {host}:{port}")
                        sock.connect((host, port))
                        print("[+] Connected.")
                        sock.sendall(b"WAITFORMECOMP<ENDING>")
                        cansend = False
                        data = b""
                        while True:
                            bytes_read = sock.recv(BUFFER_SIZE)
                            data += bytes_read
                            if(data==b'OKTOSENDORIGINALINFO<ENDING>'):
                                cansend = True
                                break
                            elif not bytes_read:
                                # file transmitting is done
                                break
                        if(not cansend):
                            print("Não foi recebida permissão para enviar pasta INFO ORIGINAL - Falhou")
                            return
                        print("Compactando pastas para o format TAR")
                        novodiretorio = os.path.dirname(dirs[0])
                        basedir = os.path.dirname(novodiretorio)
                        filenametar = 'original-{}.tar'.format(int(time.time()))
                        filenametar_abs = os.path.join(basedir, filenametar)
                        apagar.append(filenametar_abs)
                        apagar.append(filenametar)
                        #print("ttar", filenametar)
                        try:
                            iterateOverDirs(tarfile=filenametar_abs)
                        except:
                            traceback.print_exc()
                            raise Exception()
                        
                        filesize = os.path.getsize(filenametar_abs)
                        
                        #qimg = 50
                        #imgsizemin = 40
                        #vidsizemin = 1024
                        #maxdim = 1024
                        #qvid = 1
                        #send message informing the server that i want to send the latex folder
                        configs = ["0","0"]
                        if(validarjpeg):
                            configs[0] = "1"
                        if(keepfixed):
                            configs[1] = "1"
                        cfgs = configs[0]+configs[1]
                        print("Sending info from files")
                        print(f"{filenametar}{SEPARATOR}{filesize}{SEPARATOR}{qimg}{SEPARATOR}{imgsizemin}{SEPARATOR}{vidsizemin}{SEPARATOR}{maxdim}{SEPARATOR}{qvid}{SEPARATOR}{cfgs}{SEPARATOR}SENDINGORIGINAL<ENDING>")
                        sock.sendall(f"{filenametar}{SEPARATOR}{filesize}{SEPARATOR}{qimg}{SEPARATOR}{imgsizemin}{SEPARATOR}{vidsizemin}{SEPARATOR}{maxdim}{SEPARATOR}{qvid}{SEPARATOR}{cfgs}{SEPARATOR}SENDINGORIGINAL<ENDING>".encode())  
                        bytes_read = b""
                        cansend = False
                        while True:
                            bytes_read += sock.recv(BUFFER_SIZE)
                            if(bytes_read==b'OKTOSEND<ENDING>'):
                                cansend = True
                                break
                            elif not bytes_read:
                                # file transmitting is done
                                break
                        if(not cansend):
                            print("Não foi recebida permissão para enviar pasta ORIGINAL - Falhou")
                            return
                        bytesenviadostotal = 0    
                        japrintados = set()
                        parte = 0                    
                        with open(filenametar_abs, "rb") as f:                        
                            while True:                        
                                bytes_read = f.read(BUFFER_SIZE)
                                if not bytes_read:
                                    break
                                sock.sendall(bytes_read)
                                bytesenviadostotal += len(bytes_read)
                                if(round(bytesenviadostotal/filesize, 2)*100%5==0 and round(bytesenviadostotal*100/filesize) not in japrintados):
                                    japrintados.add(round(bytesenviadostotal*100/filesize))
                                    print("Enviando pasta para compressao {}%".format(round(bytesenviadostotal*100/filesize,2)))
                        print("\nAguardando retorno dos arquivos comprimidos")
                        waitingforfiles = False
                        waintforfinalreportsinfo = False
                        textprinting = True
                        data = b""
                        filename = ""
                        filesize = -1
                        while True:
                            rec = sock.recv(BUFFER_SIZE)                        
                            if not rec:    
                                break
                            else:
                                data += rec
                                if(textprinting):             
                                    if(b"ENVIANDOCOMPSINFO<ENDING>") in data:
                                        textprinting =False
                                        #let the server know that it cad send the finals reports
                                        print("Sending ok to server about compressed final info")
                                        sock.sendall(b'OKTOSENDCOMPRESSEDINFO<ENDING>')
                                        waintforfinalreportsinfo = True
                                        data = b""
                                    elif(b"Falha na execucao (server-side)<ENDING>" in data):
                                        print(data.decode())                                        
                                        print("An execution error has occured on the server side")
                                        return
                                    elif(b"<ENDING>" in data):
                                        print(data.decode())
                                        data = b""
                                elif(waintforfinalreportsinfo and b"<ENDING>" in data):
                                    waitingforfiles = True 
                                    waintforfinalreportsinfo = False
                                    data = data.decode()
                                    filename, filesize = data.split(SEPARATOR)
                                    filesize = int(filesize.replace("<ENDING>", ""))
                                    sock.sendall(b'OKTOSENDFINALCOMPRESSED<ENDING>')
                                    print(data)
                                    data = b""
                                    break
                        bytestotal = 0
                        japrintados = set()
                        novodiretorio = os.path.dirname(dirs[0])
                        basedir = os.path.dirname(novodiretorio)
                        with open(os.path.join(basedir, filename), "wb") as f:
                            while bytestotal!=filesize:
                                data = sock.recv(BUFFER_SIZE)                        
                                if not data:    
                                    raise Exception() 
                                
                                f.write(data)
                                bytestotal += len(data)
                                if(round(bytestotal/filesize, 2)*100%5==0 and round(bytestotal*100/filesize) not in japrintados):
                                    japrintados.add(round(bytestotal*100/filesize))
                                    print("Recebendo arquivos comprimidos {}%".format(round(bytestotal*100/filesize,2)))
                            print(os.path.join(novodiretorio, filename))
                            print("RECEBIDO!")
                        print("Descompactando")
                        subprocess.run("tar -xf \"{}\" -C \"{}\"".format(os.path.join(basedir, filename), basedir), check=True)
                        copyOtherFiles(verbose)
                        print("\n")
                        print("\nValidando diretórios")
                        countorg = 0
                        countnew = 0
                        validado = True
                        for diretorio in dirs:
                            validado = recursiveDirValidate(diretorio, diretorio+"-compressed", validado)
                            if(not validado):
                                break
                            #countorg = retorno[0]
                            #coutnew = retorno[1]
                        if(validado):
                            status = 0
                            print("Validado: OK")
                        else:
                            print("Validado: Falhou")
            except:
                traceback.print_exc()
            finally:
                for apa in apagar:
                    if(os.path.isfile(apa)):
                        try:
                            os.remove(apa)
                        except:
                            None
                    else:
                        try:
                            shutil.rmtree(apa)
                        except:
                            None
        elif(isserver):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                port = int(port)
                s.bind(('0.0.0.0', port))
                s.listen()
                while(True):
                    apagar = []
                    try:
                        print("Waiting")
                        probe=False
                        receivingoriginal = False
                        client_socket, address = s.accept() 
                        start_time = time.time()
                        received = b""
                        waitforme = False
                        while True:
                            bytes_read = client_socket.recv(BUFFER_SIZE)
                            received += bytes_read
                            #print(received)
                            if(b"<ENDING>") in received:
                                if b"PROBINGCOMP<ENDING>" in received:
                                    probe = True
                                    client_socket.sendall(b'AVAILABLECOMP<ENDING>')
                                    
                                elif b"WAITFORMECOMP<ENDING>":
                                    waitforme = True
                                    client_socket.sendall(b'OKTOSENDORIGINALINFO<ENDING>')
                                break
                            #elif b"SENDINGORIGINAL<ENDING>" in received:
                            #    receivingoriginal = True
                            #    break
                            elif not bytes_read:
                                break                        
                        print('recebido', received.decode())
                        if(probe):
                            print(f"[+] {address} probed.")
                            client_socket.shutdown(socket.SHUT_RDWR)
                            client_socket.close()
                        elif(waitforme):
                            print("Esperando informacoes do cliente")
                            try:
                                received = b""
                                while True:
                                    bytes_read = client_socket.recv(BUFFER_SIZE)
                                    received += bytes_read
                                    print(received)
                                    if not bytes_read:
                                        break
                                    elif b"SENDINGORIGINAL<ENDING>" in received:
                                        break
                                        #receivingoriginal = True
                                        #break
                                    
                                if b"SENDINGORIGINAL<ENDING>" in received:  
                                    received = received.decode()
                                    filename, filesize, qimg, imgsizemin, vidsizeminm, maxdim, qvid, configs, _ = received.split(SEPARATOR)
                                    validarjpeg = True
                                    if(configs[0]=="0"):
                                        validarjpeg = False
                                    keepfixed = False
                                    if(configs[1]=="1"):
                                        keepfixed = True
                                    qimg = int(qimg)
                                    imgsizemin = int(imgsizemin)
                                    vidsizemin = int(vidsizemin)
                                    maxdim = int(maxdim)
                                    qvid = int(qvid)
                                    print(f"[++++] {address} is connected.")  
                                    #give the OK to send to the client
                                    client_socket.sendall(b'OKTOSEND<ENDING>')
                                    filesize = int(filesize)
                                    bytestotal = 0
                                    with open(filename, "wb") as f:
                                        japrintados = set()
                                        while bytestotal<filesize:                                    
                                            bytes_read = client_socket.recv(BUFFER_SIZE)
                                            if not bytes_read:
                                                raise Exception()
                                            f.write(bytes_read)
                                            bytestotal += len(bytes_read)
                                            if(round(bytestotal/filesize, 2)*100%5==0 and round(bytestotal*100/filesize) not in japrintados):
                                                japrintados.add(round(bytestotal*100/filesize))
                                                print("Recebendo pasta para compressao {}%".format(round(bytestotal*100/filesize,2)))                                       
                                        #print("Escrevendo arquivo")
                                    print("Descompactando")
                                    sizeimgorg = multiprocessing.Value('i', 1)
                                    sizeimgnew = multiprocessing.Value('i', 1)
                                    sizevidorg = multiprocessing.Value('i', 1)
                                    sizevidnew = multiprocessing.Value('i', 1)
                                    #manager = multiprocessing.Manager()
                                    erros = manager.list([])
                                    listimg = manager.list([])
                                    listvid = manager.list([])
                                    listaprocesssos = manager.list([])
                                    if getattr(sys, 'frozen', False):
                                        # If the application is run as a bundle, the PyInstaller bootloader
                                        # extends the sys module by a flag frozen=True and sets the app 
                                        # path into variable _MEIPASS'.
                                        application_path = sys._MEIPASS
                                    else:
                                        application_path = os.path.dirname(os.path.abspath(__file__))
                                    apagar.append(filename)
                                    
                                    filenamenoext, extension = os.path.splitext(filename)
                                    apagar.append(filenamenoext)
                                    try:
                                        novodiretorio = os.path.join(application_path, filenamenoext, "files")
                                        apagar.append(novodiretorio)
                                        #os.makedirs(os.path.join(application_path, filename))
                                        os.makedirs(novodiretorio)
                                        subprocess.run("tar -xf \"{}\" -C \"{}\"".format(filename, novodiretorio), check=True)
                                        #apagar.append(os.path.join(application_path, filenamenoext, "files"))
                                    except:
                                        raise Exception()
                                    
                                    apagar.append(novodiretorio)
                                    apagar.append(filename)
                                    continuar = True
                                    try:
                                        print(novodiretorio)
                                        dirs = []
                                        for diretorio in os.listdir(novodiretorio):
                                            print(diretorio)
                                            if(os.path.isdir(os.path.join(novodiretorio, diretorio))):
                                                dirs.append(os.path.join(novodiretorio, diretorio))
                                        basedir = os.path.join(application_path, filenamenoext)
                                        logsDir = os.path.join(basedir, "sources", "logsCompressao")
                                        print(dirs, basedir, logsDir )
                                        if(len(dirs) == 0):
                                            break
                                        iterateOverDirs()
                                        print("Comprimindo")
                                        launchProcesses(client_socket, verbose=verbose)
                                        basedirtorun = os.path.join(application_path, filenamenoext)
                                        tarfile = filenamenoext+"-compressed.tar"
                                        apagar.append(tarfile)
                                        try:                                            
                                                
                                            subprocess.run("tar -rf \"{}\" -C \"{}\" \"{}\"".format(tarfile, basedir, "sources"), check=True)
                                        except:
                                            raise Exception()
                                        for initpath in os.listdir(novodiretorio):
                                            if("compressed" in initpath and initpath!=tarfile):
                                                relpath = os.path.relpath(os.path.join(novodiretorio, initpath), basedir)
                                                subprocess.run("tar -rf \"{}\" -C \"{}\" \"{}\"".format(tarfile, basedir, relpath), check=True)
                                        
                                                                            
                                        print("Asking permission to send compressed info")
                                        client_socket.sendall("ENVIANDOCOMPSINFO<ENDING>".encode())
                                        data = b""
                                        cansendfinalreportsinfo = False
                                        while True:
                                            bytes_read = client_socket.recv(BUFFER_SIZE)
                                           
                                            if not bytes_read:
                                                #print(data.decode())
                                                break
                                            print(data.decode())
                                            data += bytes_read
                                            if(b"OKTOSENDCOMPRESSEDINFO<ENDING>" in data):
                                                #print("Permission granted 1")
                                                cansendfinalreportsinfo = True
                                                break
                                            
                                        if(not cansendfinalreportsinfo):
                                            print("Falhou")
                                            client_socket.sendall("FALHOU".encode())
                                            raise Exception("Falhou no recebimento de autorização 1") 
                                            #return                                
                                        print("Permission granted")
                                        filesize = os.path.getsize(tarfile)
                                        #print(tarfile, filesize)
                                        print("Asking permission to send compressed")
                                        client_socket.sendall(f"{tarfile}{SEPARATOR}{filesize}<ENDING>".encode())
                                        #print(tarfile, filesize, data)
                                        
                                        data = b""
                                        cansendfinalreports = False
                                        while True:
                                            bytes_read = client_socket.recv(BUFFER_SIZE)
                                            if not bytes_read:
                                                break
                                            data += bytes_read
                                            print(data.decode())
                                            if(b"OKTOSENDFINALCOMPRESSED<ENDING>" in data):
                                                cansendfinalreports = True
                                                #print("Permission granted 2")
                                                break
                                            
                                        if(not cansendfinalreports):
                                            print("Falhou 2")
                                            client_socket.sendall("FALHOU".encode())
                                            raise Exception("Falhou no recebimento de autorização 2") 
                                        print("Permission granted 3")
                                        bytesenviados = 0
                                        with open(tarfile, "rb") as f:
                                            japrintados = set()
                                            while bytesenviados!=filesize:
                                                bytes_read = f.read(BUFFER_SIZE)
                                                if not bytes_read:
                                                    break
                                                client_socket.sendall(bytes_read)
                                                bytesenviados += len(bytes_read)
                                                if(round(bytesenviados/filesize, 2)*100%5==0 and round(bytesenviados*100/filesize) not in japrintados):
                                                    japrintados.add(round(bytesenviados*100/filesize))
                                                    print("Enviando arquivos comprimidos finais {}%".format(round(bytesenviados*100/filesize)))
                                    except:
                                        client_socket.shutdown(socket.SHUT_RDWR)
                                        client_socket.close()
                                        traceback.print_exc()
                                        print("Falhou!")
                                #sys.exit(1)
                            except:
                                traceback.print_exc()
                            finally:
                                try:
                                    client_socket.shutdown(socket.SHUT_RDWR)
                                    client_socket.close()
                                except:
                                    None
                    except:
                        traceback.print_exc()
           
                        
                        
                    finally:
                        try:
                            client_socket.shutdown(socket.SHUT_RDWR)
                            client_socket.close()
                        except:
                            None
                        for apa in apagar:
                            if(os.path.isfile(apa)):
                                try:
                                    os.remove(apa)
                                except:
                                    None
                            else:
                                try:
                                    shutil.rmtree(apa)
                                except:
                                    None
            except:
                traceback.print_exc()
            finally:                
                s.shutdown(socket.SHUT_RDWR)
                s.close()
        else:
            logsDir = os.path.join(os.path.dirname(os.path.dirname(dirs[0])), "sources", "logsCompressao")
            print(dirs)
            iterateOverDirs(None, outputdir)
            #return
            print("Comprimindo")
            launchProcesses(verbose=verbose)
            print("\nCopiando demais arquivos")
            copyOtherFiles(verbose)
            print("\n")
            print("\nValidando diretórios")
            countorg = 0
            countnew = 0
            validado = True
            for diretorio in dirs:
                diretoriosaida_inner = diretorio
                if(outputdir!=None):
                    diretoriosaida_inner = os.path.join(outputdir, os.path.basename(diretorio))
                validado = recursiveDirValidate(diretorio, diretoriosaida_inner+"-compressed", validado)
                if(not validado):
                    break
                #countorg = retorno[0]
                #coutnew = retorno[1]
            if(validado):
                status = 0
                print("Validado: OK")
            else:
                print("Validado: Falhou")
            try:
                shutil.rmtree(os.path.join(os.path.dirname(dirs[0]), "tempComp"))
            except:
                None
        
        
        
    except:
        traceback.print_exc()
    finally:
        for proc in listaprocesssos:
            try:
                proc.terminate()
            except:
                None
        try:
            logsDir = os.path.join(os.path.dirname(os.path.dirname(dirs[0])), "sources", "logsCompressao")
            with open(os.path.join(logsDir, "videos_log.txt"), "w") as videotxtlog:
                for vid in all_status_vid:
                    videotxtlog.write(f"{vid},{all_status_vid[vid]}\n")
                    
            with open(os.path.join(logsDir, "videos_img.txt"), "w") as imgtxtlog:
                for img in all_status_img:
                    imgtxtlog.write(f"{img},{all_status_img[img]}\n")
        except:
            traceback.print_exc()
        return status
    
            
        


if __name__ == '__main__':
    status = 1
    try:
        multiprocessing.freeze_support() 
        try:
            #validateJpeg()
            status = go()
        except:
            traceback.print_exc()
    except:
        #traceback.print_exc()
        None
    finally:
        sys.exit(status)