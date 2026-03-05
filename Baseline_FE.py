
import logging
import numpy as np
import pandas as pd
from scipy.stats import entropy as scipy_entropy

INPUT_FILE = "sanitized_datasetL.csv"
OUTPUT_FILE = "operator_baselines.csv"

def normalize_fc(x):
    if not x or str(x).strip() == "": return None
    s = str(x).strip().lower()
    try: return int(s, 16) if s.startswith("0x") else int(float(s))
    except Exception:
        return None         

def calc_entropy(series):
    if len(series) == 0: return 0.0
    counts = series.value_counts()
    return float(scipy_entropy(counts / len(series), base=2))

def load_data(filepath):
    df = pd.read_excel(filepath) if filepath.endswith('.xlsx') else pd.read_csv(filepath)
    df.columns = df.columns.str.strip().str.replace('\ufeff', '')
    if 'Operator_ID' in df.columns:
        df.rename(columns={'Operator_ID': 'OperatorID'}, inplace=True)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
    df["TimeInterval"] = pd.to_numeric(df["TimeInterval"], errors="coerce")
    return df

def extract_features(df):
    df["fc_int"] = df["FunctionCode"].apply(normalize_fc)
    HIGH_RISK_FC = {5,6,15,16}
    PID_COLS = ["PIDGain","PIDRate","PIDReset","PIDCycleTime","PIDDeadband"]
    records = []
    
    for (op_id, shift), grp in df.groupby(["OperatorID","Shift"]):
        grp = grp.sort_values("Timestamp").copy()
        n = len(grp)
        labels = grp["Label"].dropna().astype(str).str.strip()
        session_label = labels.mode()[0] if len(labels) > 0 else "Unknown"
        dur_sec = max((grp["Timestamp"].max() - grp["Timestamp"].min()).total_seconds(), 1)
        ti = grp["TimeInterval"][grp["TimeInterval"] > 0]
        
        CF = n / dur_sec
        IC_mean = float(ti.mean()) if len(ti) > 0 else 0.0
        IC_std = float(ti.std()) if len(ti) > 1 else 0.0
        prev_mode = grp["ControlMode"].shift(1)
        CMCR = float(((grp["ControlMode"] != prev_mode) & prev_mode.notna()).sum()) / n
        HighRisk = float(grp["fc_int"].isin(HIGH_RISK_FC).sum()) / n
        inv_fc = grp["InvalidFunctionCode"].astype(str).str.strip().str.upper()
        inv_dl = grp["InvalidDataLength"].astype(str).str.strip().str.upper()
        dl_zero = pd.to_numeric(grp["DataLength"], errors="coerce").fillna(0) == 0
        Invalid = float(((inv_fc != "X") | (inv_dl != "X") | dl_zero).sum()) / n
        pump = grp["PumpState"].astype(str).str.strip()
        prev_pump = pump.shift(1)
        PSCR = float(((pump != prev_pump) & (pump != "X") & prev_pump.notna()).sum()) / n
        sp = pd.to_numeric(grp["SetPoint"], errors="coerce")
        sp_delta = sp.diff().abs()
        sp_std = sp_delta.std()
        SP = (int((sp_delta > 2 * sp_std).sum()) if sp_std and sp_std > 0 else 0) / n
        PID = sum(int((pd.to_numeric(grp[col], errors="coerce").diff().abs() > 0).sum()) 
                  for col in PID_COLS if col in grp.columns) / n
        CBR = float((ti < 100).sum()) / n
        ENT = calc_entropy(grp["fc_int"].dropna())
        fc_seq = grp["fc_int"].dropna()
        SEQ = 0.0
        if len(fc_seq) >= 3:
            try:
                SEQ = float(pd.Series(fc_seq.values).autocorr(lag=1))
                SEQ = 0.0 if np.isnan(SEQ) else SEQ
            except: pass
        time_gaps = []
        for fc_val in grp["fc_int"].dropna().unique():
            fc_times = grp[grp["fc_int"] == fc_val]["Timestamp"]
            if len(fc_times) >= 2:
                time_gaps.extend(fc_times.diff().dt.total_seconds().dropna().tolist())
        Replay = float(np.mean(time_gaps)) if time_gaps else 0.0
        psi = pd.to_numeric(grp["PipelinePSI"], errors="coerce")
        fc = grp["fc_int"]
        valid = psi.notna() & fc.notna()
        Process_Corr = 0.0
        if valid.sum() >= 2:
            try:
                Process_Corr = float(np.corrcoef(psi[valid], fc[valid])[0, 1])
                Process_Corr = 0.0 if np.isnan(Process_Corr) else Process_Corr
            except: pass
        
        records.append({"OperatorID":op_id,"Shift":shift,"Label":session_label,
            "CF":CF,"IC_mean":IC_mean,"IC_std":IC_std,"CMCR":CMCR,"HighRisk_ratio":HighRisk,
            "Invalid_ratio":Invalid,"PSCR":PSCR,"SP":SP,"PID":PID,"CBR":CBR,"ENT":ENT,
            "SEQ":SEQ,"Replay":Replay,"Process_Corr":Process_Corr})
    
    return pd.DataFrame(records)

def build_baseline(features_df):
    baselines = []
    for op_id in sorted(features_df["OperatorID"].unique()):
        op_data = features_df[features_df["OperatorID"] == op_id]
        good = op_data[op_data["Label"] == "Good"]
        if len(good) == 0:
            good = op_data
        baseline = {"OperatorID":op_id,
            "CF_lambda":round(good["CF"].mean(),6),"CF_variance":round(good["CF"].var(),6),
            "IC_mean_mu":round(good["IC_mean"].mean(),4),"IC_mean_sigma":round(good["IC_mean"].std(),4),
            "IC_std_mu":round(good["IC_std"].mean(),4),"IC_std_sigma":round(good["IC_std"].std(),4),
            "CMCR_lambda":round(good["CMCR"].mean(),6),"CMCR_variance":round(good["CMCR"].var(),6),
            "HighRisk_ratio":round(good["HighRisk_ratio"].mean(),6),"HighRisk_sigma":round(good["HighRisk_ratio"].std(),6),
            "Invalid_ratio":round(good["Invalid_ratio"].mean(),6),"Invalid_sigma":round(good["Invalid_ratio"].std(),6),
            "PSCR_lambda":round(good["PSCR"].mean(),6),"PSCR_variance":round(good["PSCR"].var(),6),
            "SP_mu":round(good["SP"].mean(),6),"SP_sigma":round(good["SP"].std(),6),
            "PID_lambda":round(good["PID"].mean(),6),"PID_variance":round(good["PID"].var(),6),
            "CBR_lambda":round(good["CBR"].mean(),6),"CBR_variance":round(good["CBR"].var(),6),
            "ENT_mu":round(good["ENT"].mean(),6),"ENT_sigma":round(good["ENT"].std(),6),
            "SEQ_mu":round(good["SEQ"].mean(),6),"SEQ_sigma":round(good["SEQ"].std(),6),
            "Replay_mu":round(good["Replay"].mean(),4),"Replay_sigma":round(good["Replay"].std(),4),
            "Process_Corr":round(good["Process_Corr"].mean(),6),"Process_Corr_sigma":round(good["Process_Corr"].std(),6)}
        baselines.append(baseline)
    return pd.DataFrame(baselines)

def main():
    print("="*80)
    print("BASELINE PROFILE GENERATION")
    print("="*80)
    df = load_data(INPUT_FILE)
    features_df = extract_features(df)
    baseline_df = build_baseline(features_df)
    baseline_df.to_csv(OUTPUT_FILE, index=False)
    print("\n"+"="*80)
    print("BASELINES")
    print("="*80)
    print(baseline_df)
    print("\n"+"="*80)
    print(f" Saved to {OUTPUT_FILE}")
    print("="*80)

if __name__ == "__main__":
    main()
