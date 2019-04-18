#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog, tkinter.messagebox
import threading
import streamlink
from streamlink.plugins.pixiv import Pixiv as sketch
import configparser
import subprocess	#terminal操作
from time import sleep
import webbrowser
import json
import datetime

class Record(threading.Thread):
	"""
	pixivクラスのrecord_stream()で生成される。
	"""
	def __init__(self,sketch_id,folder_path):
		super().__init__()
		self.sketch_id = sketch_id.replace("@","")
		self.folder_path = folder_path
		self.dt_now = datetime.datetime.now()
		self.url = "sketch.pixiv.net/@" + sketch_id
		
	def run(self):
		file_name = self.folder_path + "/" + self.sketch_id + "_" + str(self.dt_now.year) + "_" + str(self.dt_now.month) + "_" + str(self.dt_now.day) + "_" + str(self.dt_now.minute) + ".ts"
		self.popen = subprocess.Popen(["streamlink",self.url ,"720p","-o",file_name],stdout=subprocess.PIPE)
	
	def stop(self):
		self.popen.terminate()
	
class Notification(threading.Thread):
	"""
	pixivクラスの生成時に同時に生成される。
	通知関連。
	"""
	def __init__(self,sketch_id_list):
		super().__init__()
		self.sketch_id_list = sketch_id_list
		
	def run(self):
		while True:
			for sketch_id in self.sketch_id_list:
				url = "https://sketch.pixiv.net/@" + sketch_id
				try:
					if sketch.can_handle_url(url):
						#配信中
						if len(streamlink.streams(url)) > 0:							
							if not sketch_id in pixiv.streaming_list:
								
								if pixiv.alert_record_start_value.get():
									os.system("osascript -e 'display notification \" @%s \" with title \"Pixiv Sketch\" subtitle \"配信が開始されました\" sound name \"Frog 6\"'" % sketch_id)

								#自動録画モード
								if pixiv.auto_record_value.get():
									pixiv.record_stream(sketch_id)
									sleep(1)
									
								else:
									#録画処理追加せよ
									tk.messagebox.askquestion("配信開始", "録画しますか？")
								
							
							pixiv.append_sketch_id_for_streaming_list(sketch_id)
							

				except streamlink.exceptions.PluginError:
					print("一時的にアクセスできない状態か、移動・削除されてしまった可能性があります。:" + url)
	
			sleep(int(pixiv.reload_interval_entry.get()))
				

class Pixiv(tk.Tk):
	
	def __init__(self):
		super().__init__()
				
		self.title("Pixiv dayo")
		self.geometry("500x640")
		self.resizable(False, False)

		self.notebook = ttk.Notebook(self)
		self.notebook.enable_traversal()
		
		self.tab1 = tk.Frame(self.notebook)
		self.tab2 = tk.Frame(self.notebook)
		self.tab3 = tk.Frame(self.notebook)

		self.notebook.add(self.tab1, text='メイン', padding=3)
		self.notebook.add(self.tab2, text='設定', padding=3)
		self.notebook.add(self.tab3, text='リスト', padding=3)
		self.notebook.pack(expand=1, fill=tk.BOTH)
		
		self.streaming_list = []
		self.recording_stream_list = []
		self.sketch_id_list = []
		self.record_thread_list = []
		self.sketch_id = ""
				
		#tab1------------------------------------------------------
		
		self.quick_record_label = tk.Label(self.tab1,text="@sketch_idを入力")
		self.quick_record_label.pack()
		self.sketch_id_entry = tk.Entry(self.tab1)
		self.sketch_id_entry.pack()
		self.quick_record_button = tk.Button(self.tab1,text="今すぐ録画",command=lambda:self.record_stream(self.sketch_id_entry.get()))
		self.quick_record_button.pack()
		self.recording_stream_list_label = tk.Label(self.tab1,text = "録画中の配信")
		self.recording_stream_list_label.pack()
		
		self.recording_listbox = tk.Listbox(self.tab1)
		self.recording_listbox.pack()
		
		self.stop_recording_button = tk.Button(self.tab1,text="録画を停止する",command=lambda:self.stop_record_stream(self.selecting_recording_listbox_string))
		self.stop_recording_button.pack()
		
		self.streaming_user_list_label = tk.Label(self.tab1,text = "配信中の配信")
		self.streaming_user_list_label.pack()
		self.streaming_user_listbox = tk.Listbox(self.tab1)
		self.streaming_user_listbox.pack()
		
		self.reload_streaming_user_listbox_button = tk.Button(self.tab1,text="再読み込み")
		self.reload_streaming_user_listbox_button.pack()
		
		self.open_save_folder_path_label = tk.Button(self.tab1,text="保存先フォルダを開く",command=self.open_save_folder_path)
		self.open_save_folder_path_label.pack()
		
		
		
		#tab2-----------------------------------------------------------

		self.my_sketch_id_label = tk.Label(self.tab2,text = u"自分の@sketch_id",width=5)
		self.my_sketch_id_label.grid(row=0,column=0,padx=5,pady=5,sticky=tk.EW)
		self.my_sketch_id_entry = tk.Entry(self.tab2,width=10)
		self.my_sketch_id_entry.configure(state="normal")
		self.my_sketch_id_entry.grid(row=0,column=1,padx=5,pady=5,sticky=tk.EW)		
		
		self.save_folder_path_entry = tk.Entry(self.tab2,width=30)
		self.save_folder_path_entry.configure(state="normal")
		self.save_folder_path_entry.grid(row=1,column=0,padx=0,pady=0,sticky=tk.EW)
		self.save_folder_select_button = tk.Button(self.tab2,text=u"保存先を指定",command=self.select_save_folder_of_recording_file)
		self.save_folder_select_button.grid(row=1,column=1,padx=2,pady=5,sticky=tk.W)
		
		self.reload_interval_label = tk.Label(self.tab2,text = u"リロード間隔(10以上)",width=5)
		self.reload_interval_label.grid(row=2,column=0,padx=5,pady=5,sticky=tk.EW)	
		self.reload_interval_entry = tk.Entry(self.tab2,width=3)
		self.reload_interval_entry.configure(state="normal")
		self.reload_interval_entry.grid(row=2,column=1,padx=5,pady=5,sticky=tk.EW)
		
		self.auto_record_checkbox = tk.Checkbutton(self.tab2,text=u"自動で録画")
		self.auto_record_checkbox.grid(row=3,column=0,padx=1,pady=5)
		
		self.alert_record_start_checkbox = tk.Checkbutton(self.tab2,text=u"配信の開始を通知")
		self.alert_record_start_checkbox.grid(row=3,column=1,padx=1,pady=5)
		
		self.save_option_settings_button = tk.Button(self.tab2,text=u"変更を保存",command=self._reflect_app_settings)
		self.save_option_settings_button.grid(row=99,column=1,columnspan=1,padx=1,pady=5,sticky=tk.NE)
		
		#tab3--------
		
		self.watch_list_sketch_id_label = tk.Label(self.tab3,text=u"@sketch_idを入力")
		self.watch_list_sketch_id_label.pack()
		self.watch_list_sketch_id_entry = tk.Entry(self.tab3)
		self.watch_list_sketch_id_entry.pack()
		
		self.quick_record_button = tk.Button(self.tab3,text="追加",command=self.append_sketch_id_for_watchlist)
		self.quick_record_button.pack()
		self.watch_list_label = tk.Label(self.tab3,text = "ウォッチリスト")
		self.watch_list_label.pack()
		self.sketch_id_listbox = tk.Listbox(self.tab3)
		self.sketch_id_listbox.pack()		
		
		self.delete_watch_list_id_button = tk.Button(self.tab3,text="選択したidを削除",command=self.delete_selected_index_in_listbox)
		self.delete_watch_list_id_button.pack()
		self.delete_watch_list_id_all_button = tk.Button(self.tab3,text="全てのidを削除",command=lambda:self.delete_selected_index_in_listbox(True))
		self.delete_watch_list_id_all_button.pack()

		self._reflect_config_settings()
		self.bind("<ButtonRelease-1>",self._get_all_indexes_in_listbox)		
		
		notification = Notification(self.sketch_id_list)
		notification.start()
		
		

		
	def _reflect_config_settings(self):
		"""
		config.iniの設定をアプリに反映する。
		"""
		
		for sketch_id in json.loads(config.get("general", "sketch_id_list")):
			self.sketch_id_listbox.insert(tk.END,sketch_id)
			self.sketch_id_list.append(sketch_id)
			
		
		self.my_sketch_id_entry.insert(0,config.get("general", "sketch_id"))
		self.folder_path = config.get("setting", "save_folder")

		self.save_folder_path_entry.insert(0,self.folder_path)	
		self.save_folder_path_entry.configure(state="readonly")
		
		self.reload_interval_entry.insert(0,config.get("setting", "reload_interval"))	

		
		#チェックボックス系
		self.auto_record_value = tk.BooleanVar()
		self.alert_record_start_value = tk.BooleanVar()
		boolean = self.convert_to_boolean_from_string(config.get("setting", "auto_record"))
		self.auto_record_value.set(boolean)
		self.auto_record_checkbox.configure(variable=self.auto_record_value)
		boolean = self.convert_to_boolean_from_string(config.get("setting", "alert_stream"))
		self.alert_record_start_value.set(boolean)
		self.alert_record_start_checkbox.configure(variable=self.alert_record_start_value)
		
	def _reflect_app_settings(self):
		"""
		アプリの設定をconfig.iniに反映する。
		"""
		
		
		config.set(u"general",u"sketch_id",self.my_sketch_id_entry.get())
		"""
		sketch_ids_string = ""
		for sketch_id in self.sketch_id_list:
			sketch_ids_string+= '"' + sketch_id + '",'
		sketch_ids_string = "[" + sketch_ids_string[:-1] + "]"	
		"""
		
		sketch_ids_string = "[" + ",".join(['"' + sketch_id + '"' for sketch_id in self.sketch_id_list])  + "]"	
		config.set(u"general", u"sketch_id",self.my_sketch_id_entry.get())
		config.set(u"general",u"sketch_id_list",sketch_ids_string)	
		config.set(u"setting",u"save_folder",self.folder_path)
		config.set(u"setting",u"auto_record",str(self.auto_record_value.get()))
		config.set(u"setting",u"alert_stream",str(self.alert_record_start_value.get()))
		config.set(u"setting",u"reload_interval",int(self.reload_interval_entry.get()))

		f = open('pixiv_config.ini', 'w')
		config.write(f)
		f.close()
		
		
	def _get_all_indexes_in_listbox(self,event):
		"""
		listboxの要素をクリックした時に、全てのlistboxの選択している要素を更新する。
		"""
		
		self.selecting_recording_listbox_index = self.recording_listbox.index(tk.ACTIVE)
		self.selecting_recording_listbox_string = self.recording_listbox.get(tk.ACTIVE)
		self.selecting_streaming_user_listbox_index = self.streaming_user_listbox.index(tk.ACTIVE)
		self.selecting_streaming_user_listbox_string = self.streaming_user_listbox.get(tk.ACTIVE)
		self.selecting_sketch_id_listbox_index = self.sketch_id_listbox.index(tk.ACTIVE)								
		self.selecting_sketch_id_listbox_string = self.sketch_id_listbox.get(tk.ACTIVE)	

	def convert_to_boolean_from_string(self,string):
		"""
		config.iniの文字列をbooleanに変換する。
		
		Parameters
		
		----------
		
		string : string
			config.iniの変換したい文字列。
		"""
		if string == "True":
			return True
		else:
			return False
	
	def select_save_folder_of_recording_file(self):
		"""
		録画ファイルの保存先を設定する。
		"""
		
		folder = tk.filedialog.askdirectory()
		
		self.folder_path = os.path.abspath(folder)
		self.save_folder_path_entry.configure(state="normal")
		self.save_folder_path_entry.delete(0,tk.END)
		self.save_folder_path_entry.insert(0,self.folder_path)	
		self.save_folder_path_entry.configure(state="readonly")
		
		self._reflect_app_settings()
		
	def record_stream(self,sketch_id):
		"""
		録画を開始する。
		
		Parameters
		
		----------
		
		sketch_id : string
			PixivSketchのid。
		"""
		
		if not sketch_id in self.recording_stream_list:
			print("録画を開始します:" + sketch_id)
			record = Record(sketch_id,self.folder_path)
			record.start()
			
			self.recording_stream_list.append(sketch_id)
			self.recording_listbox.insert(tk.END, sketch_id)
			self.record_thread_list.append(record)
			print(self.record_thread_list[0].sketch_id)
			
	def stop_record_stream(self,sketch_id):
		for thread in self.record_thread_list:
			if sketch_id in thread.sketch_id:
				thread.stop()
				self.recording_stream_list.remove(sketch_id)
				self.recording_listbox.delete("active")
	def append_sketch_id_for_watchlist(self):
		"""
		ウォッチリストにsketchIDを追加する。
		"""
		inputted_sketch_id = self.watch_list_sketch_id_entry.get()
		self.sketch_id_listbox.insert(tk.END,inputted_sketch_id)
		
		#self.sketch_id_listを更新
		self.sketch_id_list = [ sketch_id for sketch_id in json.loads(config.get("general", "sketch_id_list"))]
		self.sketch_id_list.append(inputted_sketch_id)
				
		self._reflect_app_settings()
		
	def append_sketch_id_for_streaming_list(self,streaming_sketch_id):
		"""
		配信中リストにsketchIDを追加する。
		"""
		if not streaming_sketch_id in self.streaming_list:
			self.streaming_list.append(streaming_sketch_id)
			self.streaming_user_listbox.insert(tk.END,streaming_sketch_id)
			
	def delete_selected_index_in_listbox(self,delete_all = False):
		"""
		ウォッチリストのsketchIDを削除する。
		
		Parameters
		
		----------
		
		boolean : delete_all
		Trueなら項目を全て削除する。
		"""
		if delete_all:
			self.sketch_id_listbox.delete(0,tk.END)
			self.sketch_id_list = []
		else:
			self.sketch_id_listbox.delete(self.selecting_sketch_id_listbox_index)
			self.sketch_id_list.remove(self.selecting_sketch_id_listbox_string)
			
		self._reflect_app_settings()
		
		
	def open_save_folder_path(self):
		"""
		録画ファイルの保存先ディレクトリをfinderで開く。
		"""
		try:
			webbrowser.open("file://" + self.folder_path)
		except AttributeError:
			print("フォルダがない...")
		
if __name__ == "__main__":
	
	config = configparser.SafeConfigParser()
	config.read("pixiv_config.ini",encoding="utf8")	
	
	pixiv = Pixiv()
	pixiv.mainloop()