import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
def segment(journeys,k=4):
    if len(journeys)<k:return []
    rows=[{"length":j.journey_length,"duration":j.duration_seconds,"unique":j.unique_pages,"repeat":j.repeated_pages,"loops":j.loop_count,"converted":int(j.converted)} for j in journeys]
    df=pd.DataFrame(rows); cols=["length","duration","unique","repeat","loops"]
    labels=KMeans(n_clusters=k,random_state=42,n_init=10).fit_predict(StandardScaler().fit_transform(df[cols]));df["cluster"]=labels
    out=[]
    for c,g in df.groupby("cluster"):
        conv=g.converted.mean()*100
        label="Fast Converters" if conv>=60 and g.length.mean()<=df.length.median() else "Researchers" if g.length.mean()>=df.length.quantile(.75) else "Lost Users" if conv<25 else "Hesitant Users"
        out.append({"segment":label,"users":len(g),"percentage":round(len(g)/len(df)*100,2),"avg_journey_length":round(g.length.mean(),2),"avg_duration":round(g.duration.mean(),2),"conversion_rate":round(conv,2),"characteristics":cols})
    return out
