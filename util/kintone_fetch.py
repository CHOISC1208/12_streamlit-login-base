import json
import os
import requests
import pandas as pd

class KintoneConfigLoader:
    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__),
            'kintone_config.json'
        )
        print(f"設定ファイルのパス: {self.config_path}")
        self.settings = self._load_config()
    
    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"設定ファイル '{self.config_path}' が見つかりません。"
            )
    
    def get_settings(self, environment='production'):
        """指定された環境の設定を取得する"""
        if environment not in self.settings:
            raise ValueError(f"環境設定 '{environment}' が見つかりません。"
                           f"利用可能な環境: {list(self.settings.keys())}")
        return self.settings[environment]

class KintoneDataManager:
    def __init__(self, environment='production'):
        config_loader = KintoneConfigLoader()
        settings = config_loader.get_settings(environment)
        self.base_url = settings['base_url']
        self.configs = settings['configs']
        self.dataframes = None
    
    def fetch_data(self):
        """すべてのデータを取得して処理する"""
        print("\nkintone APIの制限事項:")
        print("=" * 40)
        print("- 1回のリクエストの最大取得件数: 500件")
        print("- offset上限値: 10,000件")
        print("- 検索結果上限: 100,000件")
        print("=" * 40)
        
        all_data = self._fetch_all_kintone_data()
        self.dataframes = self._merge_dataframes(all_data)
        
        print("\n取得したデータフレーム一覧:")
        print("=" * 40)
        for df_name, df in self.dataframes.items():
            record_count = len(df)
            status = "⚠️ 制限に近い" if record_count > 9000 else "✓"
            print(f"- {df_name:<30} ({record_count:>6,} 行) {status}")
        print("=" * 40 + "\n")
        
        return self
    
    def get_dataframe(self, name):
        """単一のデータフレームを取得"""
        if self.dataframes is None:
            raise ValueError("データフレームが初期化されていません。fetch_data()を先に実行してください。")
        return self.dataframes.get(name.strip())

    def get_multiple_dataframes(self, *names):
        """複数のデータフレームを一度に取得"""
        if self.dataframes is None:
            raise ValueError("データフレームが初期化されていません。fetch_data()を先に実行してください。")
        return [self.get_dataframe(name) for name in names]
    
    def get_available_dataframes(self):
        """利用可能なデータフレーム名の一覧を返す"""
        if self.dataframes is None:
            raise ValueError("データフレームが初期化されていません。fetch_data()を先に実行してください。")
        return list(self.dataframes.keys())

    def show_dataframe_info(self):
        """データフレームの詳細情報を表示"""
        print("\n利用可能なデータフレーム一覧:")
        print("=" * 40)
        for df_name, df in self.dataframes.items():
            print(f"- {df_name:<30} ({len(df):>6,} 行)")
        print("=" * 40 + "\n")
    
    def _process_main_field(self, main_row, key, value):
        if value['type'] in ['CREATOR', 'MODIFIER']:
            main_row[f'{key}_code'] = value['value']['code']
            main_row[f'{key}_name'] = value['value']['name']
        elif isinstance(value['value'], dict):
            for subkey, subvalue in value['value'].items():
                main_row[f'{key}_{subkey}'] = subvalue
        else:
            main_row[key] = value['value']
    
    def _process_subtable(self, record, key, value, sub_data_dict):
        subtable = value['value']
        if key not in sub_data_dict:
            sub_data_dict[key] = []
        for subrecord in subtable:
            sub_row = {subkey: subvalue['value'] for subkey, subvalue in subrecord['value'].items()}
            sub_row['main_id'] = record['$id']['value']
            sub_data_dict[key].append(sub_row)
    
    def _fetch_kintone_records(self, app_no, apitoken, query='', limit=500):
        headers = {"X-Cybozu-API-Token": apitoken}
        offset = 0
        records = []
        total_records = 0

        print(f"\nレコード取得中... (limit={limit})")
        while True:
            params = {
                "app": app_no,
                "query": query + f" limit {limit} offset {offset}"
            }
            
            ret = requests.get(self.base_url, headers=headers, params=params)
            if ret.status_code != 200:
                ret.raise_for_status()
            batch_records = ret.json().get('records', [])
            
            if not batch_records:
                break
                
            records.extend(batch_records)
            total_records += len(batch_records)
            print(f"- {offset}～{offset + len(batch_records)}件目を取得 (現在合計: {total_records}件)")
            
            offset += limit
        
        print(f"取得完了: 合計{total_records}件\n")
        return self._process_records(records)
    
    def _process_records(self, records):
        main_data = []
        sub_data_dict = {}
        
        for record in records:
            # メインテーブルのデータ処理
            main_row = {}
            for key, value in record.items():
                if value['type'] == 'SUBTABLE':
                    # サブテーブルの処理
                    self._process_subtable(record, key, value, sub_data_dict)
                else:
                    # メインテーブルの処理
                    self._process_main_field(main_row, key, value)
            main_data.append(main_row)
        
        # メインテーブルのDataFrame作成
        df_main = pd.DataFrame(main_data)
        
        # サブテーブルのDataFrame作成
        df_sub_tables = {
            f'df_sub_{i+1}': pd.DataFrame(data) 
            for i, data in enumerate(sub_data_dict.values())
        }
        
        return df_main, df_sub_tables
    
    def _fetch_all_kintone_data(self):
        return {key: {'main': main_df, 'sub_tables': sub_dfs}
                for key, config in self.configs.items()
                for main_df, sub_dfs in [self._fetch_kintone_records(
                    config['app_no'], config['apitoken'], config['query'])]}
    
    def _merge_dataframes(self, all_data):
        merged_dataframes = {}
        for config_name, data in all_data.items():
            # メインテーブルを追加
            merged_dataframes[f"{config_name}_main"] = data['main']
            
            # サブテーブルを追加
            for sub_name, sub_df in data['sub_tables'].items():
                if sub_df is not None:
                    merged_df_name = f"{config_name}_{sub_name}"
                    merged_df = sub_df.merge(data['main'], how='left', left_on='main_id', right_on='$id')
                    merged_dataframes[merged_df_name] = merged_df
        
        return merged_dataframes
