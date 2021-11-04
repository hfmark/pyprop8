import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pyprop8 as pp
from pyprop8.utils import make_moment_tensor,rtf2xyz
from mpl_toolkits.mplot3d import Axes3D

class tqdm_dropin:
    def __init__(self,total):
        self.st = st.progress(total)
        self.value = 0
    def update(self,n):
        self.value+=n
        self.st.progress(self.value)

def parse_text_model(txt):
    lines = txt.lstrip().rstrip().split('\n')
    model = []
    for line in lines:
        line = line.lstrip()
        if len(line)==0: continue
        if line[0]=='#': continue

        words = line.split()
        if len(words)!=4:
            raise ValueError
        try:
            model += [tuple(float(w) for w in words)]
        except ValueError:
            if words[0].lower() == 'np.inf':
                model += [(np.inf,)+tuple(float(w) for w in words[1:])]
            else:
                raise ValueError("Unable to parse model.")
    return model


st.write("Hello! Welcome to pyprop8!")
with st.sidebar: #.form("Source parameters"):
    strike = st.slider("Strike:",1,360)
    dip = st.slider("Dip:",0,90)
    rake = st.slider("Rake:",0,90)
    eventdepth = st.slider("Event depth:",5,100)
    recdepth = st.slider("Receiver depth:",0,50)
    Mw = st.slider("Magnitude:",4.,10.,step=0.1)
    #submitted = st.form_submit_button("Go!")
    cmax = st.slider("Colorscale max:",1,100)

with st.sidebar.form("Earth structure"):
    textmodel = st.text_area("Enter model",
                    value='inf 5. 3. 2.',
                    help='')
    textfmt = st.radio('Format:',('Thickness','Interface depth'))
    model_submitted = st.form_submit_button("Go!")


M0 = 10**(3*(Mw+10.7)/2 - 19)
M = rtf2xyz(make_moment_tensor(strike,dip,rake,M0,0,0))


source = pp.PointSource(0.,0.,float(eventdepth),M,np.zeros([3,1]),0)
try:
    model = pp.LayeredStructureModel(parse_text_model(textmodel),interface_depth_form=(textfmt=='Interface depth'))
except ValueError:
    st.error("Unable to parse model!\n\nPlease check that it is correctly formatted.")
    st.stop()

stations = pp.RegularlyDistributedReceivers(1,100,100,0,360,360,depth=float(recdepth))
with st.spinner("Reticulating splines..."):
    static = pp.compute_static(model,source,stations)
fig = plt.figure()
#ax = fig.add_axes((0,0,1,1),projection='3d')
ax = fig.add_subplot(111)
ax.set_aspect(1.0)
pts = ax.scatter(*stations.as_xy(),c=static[:,:,2],cmap=plt.cm.coolwarm,s=2)
#xx,yy = stations.as_xy()
#pts = ax.plot_trisurf(xx.flatten(),yy.flatten(),static[:,:,2].flatten(),cmap=plt.cm.coolwarm)
#ax.quiver(xx,yy,np.zeros_like(xx),1e1*static[:,:,0],1e2*static[:,:,1],0*static[:,:,2])
ax.plot([0],[0],marker='*',mfc='k',mec='k',lw=0,markersize=10)
ax.set_xlabel("East --- West")
ax.set_xlim(-100,100)
ax.set_yticks([-100,0,100])
ax.set_ylabel("South --- North")
ax.set_ylim(-100,100)
ax.set_xticks([-100,0,100])
pts.set_clim(-cmax,cmax)
cax = fig.add_axes((0.65,0.1,0.2,0.025))
plt.colorbar(pts,cax=cax,label='Displacement (mm)',orientation='horizontal',ticks=[-cmax,0,cmax])
st.pyplot(fig)
st.caption("Vertical-component static offset")
st.text(model)
