from Scripts import *
import os, plistlib, json, datetime, sys

try:
    long
    unicode
except NameError:  # Python 3
    long = int
    unicode = str

class OCCC:
    def __init__(self):
        self.d = downloader.Downloader()
        self.u = utils.Utils("OC配置比较器（宿命汉化）")
        if 2/3 == 0: self.dict_types = (dict,plistlib._InternalDict)
        else: self.dict_types = (dict)
        self.current_config = None
        self.current_plist  = None
        self.sample_plist   = None
        self.sample_url     = "https://github.com/acidanthera/OpenCorePkg/raw/master/Docs/Sample.plist"
        self.sample_path    = os.path.join(os.path.dirname(os.path.realpath(__file__)),os.path.basename(self.sample_url))
        self.settings_file  = os.path.join(os.path.dirname(os.path.realpath(__file__)),"Scripts","settings.json")
        self.settings       = {} # Smol settings dict - { "hide_with_prefix" : "#" }
        if os.path.exists(self.settings_file):
            try: self.settings = json.load(open(self.settings_file))
            except: pass
        self.sample_config  = self.sample_path if os.path.exists(self.sample_path) else None
        if self.sample_config:
            try:
                with open(self.sample_config,"rb") as f:
                    self.sample_plist = plist.load(f)
            except:
                self.sample_plist = self.sample_config = None

    def is_data(self, value):
        return (sys.version_info >= (3, 0) and isinstance(value, bytes)) or (sys.version_info < (3,0) and isinstance(value, plistlib.Data))

    def get_type(self, value):
        if isinstance(value, dict):
            return "Dictionary"
        elif isinstance(value, list):
            return "Array"
        elif isinstance(value, datetime.datetime):
            return "Date"
        elif self.is_data(value):
            return "Data"
        elif isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, (int,long)):
            return "Integer"
        elif isinstance(value, float):
            return "Real"
        elif isinstance(value, (str,unicode)):
            return "String"
        else:
            return str(type(value))

    def compare(self):
        # First make sure we have plist info
        c = self.get_plist("user config.plist",self.current_config)
        if c is None:
            return
        self.current_config,self.current_plist = c
        # Get the latest if we don't have one - or use the one we have
        if self.sample_config is None:
            s = self.get_latest(False)
        else:
            s = self.get_plist("OC Sample.plist",self.sample_config)
        if s is None:
            return
        self.sample_config,self.sample_plist = s
        self.u.head()
        print("")
        print("检查用户plist中缺少的值:")
        print("")
        changes = self.compare_value(self.sample_plist,self.current_plist,os.path.basename(self.current_config))
        if len(changes):
            print("\n".join(changes))
        else:
            print(" - 用户配置中没有丢失任何内容！")
        print("")
        print("检查示例plist中是否缺少值：")
        print("")
        changes = self.compare_value(self.current_plist,self.sample_plist,os.path.basename(self.sample_config))
        if len(changes):
            print("\n".join(changes))
        else:
            print(" - 示例配置中没有缺少任何内容！")
        print("")
        self.u.grab("按[enter]键返回...")

    def compare_value(self, compare_from, compare_to, path=""):
        change_list = []
        # Compare 2 collections and print anything that's in compare_from that's not in compare_to
        if type(compare_from) != type(compare_to):
            change_list.append("{} - Type Difference: {} --> {}".format(path,self.get_type(compare_to),self.get_type(compare_from)))
            return change_list # Can't compare further - they're not the same type
        if isinstance(compare_from,self.dict_types):
            # Let's compare keys
            not_keys = [x for x in list(compare_from) if not x in list(compare_to)]
            if self.settings.get("hide_with_prefix","#") != None:
                not_keys = [x for x in not_keys if not x.startswith(self.settings.get("hide_with_prefix","#"))]
            if not_keys:
                for x in not_keys:
                    change_list.append("{} - Missing Key: {}".format(path,x))
            # Let's verify all other values if needed
            for x in list(compare_from):
                if x in not_keys: continue # Skip these as they're already not in the _to
                if self.settings.get("hide_with_prefix","#") != None and x.startswith(self.settings.get("hide_with_prefix","#")): continue # Skipping this due to prefix
                val  = compare_from[x]
                val1 = compare_to[x]
                if type(val) != type(val1):
                    change_list.append("{} - Type Difference: {} --> {}".format(path+" -> "+x,self.get_type(val1),self.get_type(val)))
                    continue # Move forward as all underlying values will be different too
                if isinstance(val,list) or isinstance(val,self.dict_types):
                    change_list.extend(self.compare_value(val,val1,path+" -> "+x))
        elif isinstance(compare_from,list):
            # This will be tougher, but we should only check for dict children and compare keys
            if not len(compare_from) or not len(compare_to): return change_list # Nothing to do here
            if isinstance(compare_from[0],self.dict_types):
                # Let's compare keys
                change_list.extend(self.compare_value(compare_from[0],compare_to[0],path+" -> "+"Array"))
        return change_list

    def get_latest(self,wait=True):
        self.u.head()
        print("")
        print("正在收集最新的 sample.plist：")
        print(self.sample_url)
        print("")
        p = None
        dl_config = self.d.stream_to_file(self.sample_url,self.sample_path)
        if not dl_config:
            print("\n下载失败！\n")
            if wait: self.u.grab("按[enter]键返回...")
            return None
        print("等待...")
        try:
            with open(dl_config,"rb") as f:
                p = plist.load(f)
        except Exception as e:
            print("\nPlist 加载失败:  {}\n".format(e))
            if wait: self.u.grab("按[enter]键返回...")
            return None
        print("")
        if wait: self.u.grab("按[enter]键返回...")
        return (dl_config,p)

    def get_plist(self,plist_name="config.plist",plist_path=None):
        while True:
            if plist_path != None:
                m = plist_path
            else:
                self.u.head()
                print("")
                print("M. 返回菜单")
                print("Q. 退出")
                print("")
                m = self.u.grab("请拖放 {} 文件:  ".format(plist_name))
                if m.lower() == "m":
                    return None
                elif m.lower() == "q":
                    self.u.custom_quit()
            plist_path = None # Reset
            pl = self.u.check_path(m)
            if not pl:
                self.u.head()
                print("")
                self.u.grab("路径不存在！",timeout=5)
                continue
            try:
                with open(pl,"rb") as f:
                    p = plist.load(f)
            except Exception as e:
                self.u.head()
                print("")
                self.u.grab("Plist ({}) 加载失败:  {}".format(os.path.basename(pl),e),timeout=5)
                continue
            return (pl,p) # Return the path and plist contents

    def custom_hide_prefix(self):
        self.u.head()
        print("")
        print("隐藏快捷键前缀: {}".format(self.settings.get("hide_with_prefix","#")))
        print("")
        pref = self.u.grab("请输入自定义快捷键前缀： ")
        return pref if len(pref) else None

    def hide_key_prefix(self):
        self.u.head()
        print("")
        print("隐藏快捷键前缀: {}".format(self.settings.get("hide_with_prefix","#")))
        print("")
        print("1. 隐藏快捷键 #")
        print("2. 输入自定义快捷键")
        print("3. 显示所有快捷键")
        print("")
        print("M. 返回菜单")
        print("Q. 退出")
        print("")
        menu = self.u.grab("请选择一个选项： ")
        if menu.lower() == "m": return
        elif menu.lower() == "q": self.u.custom_quit()
        elif menu == "1":
            self.settings["hide_with_prefix"] = "#"
            self.save_settings()
        elif menu == "2":
            self.settings["hide_with_prefix"] = self.custom_hide_prefix()
            self.save_settings()
        elif menu == "3":
            self.settings["hide_with_prefix"] = None
            self.save_settings()
        self.hide_key_prefix()

    def save_settings(self):
        try: json.dump(self.settings,open(self.settings_file,"w"),indent=2)
        except: pass

    def main(self):
        self.u.head()
        print("")
        print("当前配置:   {}".format(self.current_config))
        print("OC 示例配置: {}".format(self.sample_config))
        print("隐藏快捷键前缀: {}".format(self.settings.get("hide_with_prefix","#")))
        print("")
        print("1. 更改快捷键前缀")
        print("2. 获取最新 Sample.plist")
        print("3. 选择自定义 Sample.plist")
        print("4. 选择用户 Config.plist")
        print("5. 比较（将使用最新的Sample.plist如果未选择）")
        print("")
        print("Q. 退出")
        print("")
        m = self.u.grab("请选择一个选项:  ").lower()
        if m == "q":
            self.u.custom_quit()
        elif m == "1":
            self.hide_key_prefix()
        elif m == "2":
            p = self.get_latest()
            if p is not None:
                self.sample_config,self.sample_plist = p
        elif m == "3":
            p = self.get_plist("OC示例 Sample.plist")
            if p is not None:
                self.sample_config,self.sample_plist = p
        elif m == "4":
            p = self.get_plist("用户 config.plist")
            if p is not None:
                self.current_config,self.current_plist = p
        elif m == "5":
            self.compare()

if __name__ == '__main__':
    if 2/3 == 0:
        input = raw_input
    o = OCCC()
    while True:
        try:
            o.main()
        except Exception as e:
            print("\nError: {}\n".format(e))
            input("按[enter]键返回...")
