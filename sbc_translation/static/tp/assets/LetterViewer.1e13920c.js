var b=Object.defineProperty;var w=(l,s,e)=>s in l?b(l,s,{enumerable:!0,configurable:!0,writable:!0,value:e}):l[s]=e;var t=(l,s,e)=>(w(l,typeof s!="symbol"?s+"":s,e),e);import{C as f,x as u,M as y,B as h,u as x,m as v,n as p,_ as c,L as g,I as z,R as L,d as C,f as o,b as I,j as M,e as B,o as k,k as P,l as T}from"./index.79c05fa8.js";import{T as D}from"./TranslatorButton.809c59a7.js";class r extends f{constructor(){super(...arguments);t(this,"state",x({loading:!1,message:"",type:null,types:[]}))}setup(){this.state.loading=!0,v.settings.letterIssues().then(e=>{this.state.types=e,this.state.type=e[0].id,this.state.loading=!1})}async submit(){if(!this.state.type){p.error(c("Please select a problem in the list"));return}this.state.loading=!0;const e=await v.letters.reportIssue(this.props.letterId,this.state.type,this.state.message);this.state.loading=!1,e?(p.success(c("Issue successfully sent, it will be quickly reviewed")),this.props.onClose()):p.error(c("Unable to submit issue"))}}t(r,"template",u`  
    <Modal active="props.active" onClose="props.onClose" title="'Signal a Problem'" subtitle="'Notify Compassion of a problem with this letter'" loading="state.loading">
      <div class="p-4 signal-problem-modal">
        <select class="compassion-input text-sm mb-2" t-model="state.type">
          <option t-foreach="state.types" t-as="type" t-key="type.id" t-att-value="type.id" t-esc="type.text" />
        </select>
        <textarea class="compassion-input text-sm" t-model="state.message" placeholder="Your Message" />
      </div>
      <t t-set-slot="footer-buttons">
        <Button color="'compassion'" size="'sm'" onClick="() => this.submit()">Send Message</Button>
      </t>
    </Modal>
  `),t(r,"props",{letterId:{},active:{type:Boolean},onClose:{type:Function}}),t(r,"components",{Modal:y,Button:h});class n extends f{}t(n,"template",u`
    <div t-if="props.letter" id="letter-viewer-header">
      <div class="flex bg-white relative border-b border-solid border-slate-300">
        <div class="pt-3 pb-5 px-4 mr-10">
          <h4 class="font-semibold text-gray-800 mb-2 text-lg">Child Data</h4>
          <div class="flex text-sm mb-1 text-slate-800">
            <p class="w-32  font-medium">Preferred Name</p>
            <p class="" t-esc="props.letter.child.preferredName" />
          </div>
          <div class="flex text-sm mb-1 text-slate-800">
            <p class="w-32  font-medium">Full Name</p>
            <p class="" t-esc="props.letter.child.fullName" />
          </div>
          <div class="flex text-sm mb-1 text-slate-800">
            <p class="w-32  font-medium">Sex</p>
            <p class="" t-esc="props.letter.child.sex === 'M' ? 'Man' : 'Woman'" />
          </div>
          <div class="flex text-sm text-slate-800">
            <p class="w-32  font-medium">Age</p>
            <p class="" t-esc="(props.letter.child.age) + ' Years Old'" />
          </div>
        </div>
        <div class="py-3 px-4 mr-10">
          <h4 class="font-semibold text-gray-800 mb-2 text-lg">Sponsor Data</h4>
          <div class="flex text-sm mb-1 text-slate-800">
            <p class="w-32  font-medium">Preferred Name</p>
            <p class="" t-esc="props.letter.sponsor.preferredName" />
          </div>
          <div class="flex text-sm mb-1 text-slate-800">
            <p class="w-32  font-medium">Full Name</p>
            <p class="" t-esc="props.letter.sponsor.fullName" />
          </div>
          <div class="flex text-sm mb-1 text-slate-800">
            <p class="w-32  font-medium">Sex</p>
            <p class="" t-esc="props.letter.sponsor.sex === 'M' ? 'Man' : 'Woman'" />
          </div>
          <div class="flex text-sm text-slate-800">
            <p class="w-32  font-medium">Age</p>
            <p class="" t-esc="(props.letter.sponsor.age) + ' Years Old'" />
          </div>
        </div>
        <div class="py-3 px-4 flex-1">
          <h4 class="font-semibold text-gray-800 mb-2 text-lg">Letter Information</h4>
          <div class="flex text-sm mb-1 text-slate-800">
            <p class="w-32  font-medium">Title</p>
            <p class="" t-esc="props.letter.title" />
          </div>
          <div class="flex text-sm mb-1 text-slate-800">
            <p class="w-32  font-medium">Identifier</p>
            <p class="" t-esc="props.letter.id" />
          </div>
          <div class="flex text-sm mb-1 text-slate-800">
            <p class="w-32  font-medium">Language</p>
            <p class="">
              <span t-esc="props.letter.source" />
              <span class="font-semibold mx-1">-></span>
              <span t-esc="props.letter.target" />
            </p>
          </div>
          <div class="flex text-sm text-slate-800">
            <p class="w-32  font-medium">Translator</p>
            <TranslatorButton t-if="props.letter.translatorId" translatorId="props.letter.translatorId" />
          </div>
        </div>
      </div>
    </div>
    <div class="bg-slate-100 px-4 py-3 border-b border-solid border-slate-300 flex justify-between shadow-sm items-center z-20 relative">
      <div t-if="props.letter" class="flex items-center gap-2">
        <span class="rounded-sm py-0.5 px-1 text-xs font-medium text-white bg-slate-500" t-esc="props.letter.status" />
        <p class="text-sm text-slate-600">
          <t t-if="props.letter.lastUpdate">
            Last updated the <span t-esc="props.letter.lastUpdate.toLocaleString()" />
          </t>
          <span t-else="">Never Modified</span>
        </p>
        <Loader t-if="props.loading" />
      </div>
      <div class="flex gap-3 items-center">
        <t t-slot="default" />
      </div>
    </div>
  `),t(n,"components",{Loader:g,TranslatorButton:D}),t(n,"props",{letter:{type:Object,optional:!0},slots:{optional:!0},loading:{type:Boolean,optional:!0}});const S={letter:{type:Object,optional:!0},letterId:{optional:!1},loading:{type:Boolean,optional:!0},smallLoading:{type:Boolean,optional:!0},slots:{optional:!0}};class m extends f{constructor(){super(...arguments);t(this,"letterPanel",o("letterPanel"));t(this,"panelDrag",o("panelDrag"));t(this,"infoHeader",o("header"));t(this,"contentContainer",o("contentContainer"));t(this,"currentTranslator",I());t(this,"resizeCallback",null);t(this,"onMouseUp",null);t(this,"onMouseDown",null);t(this,"dragInitialized",!1);t(this,"dx",0);t(this,"state",x({mode:"letter",displayHeight:0,active:!1,signalProblemModal:!1}))}setup(){this.currentTranslator.loadIfNotInitialized(),this.resizeCallback=e=>this.resize(e),this.onMouseUp=()=>{document.removeEventListener("mousemove",this.resizeCallback,!1),this.state.active=!1},this.onMouseDown=e=>{this.dx=e.x,this.state.active=!0,document.addEventListener("mousemove",this.resizeCallback,!1)},M(()=>{const e=()=>this.computeContainerSize();return window.addEventListener("resize",e),()=>window.removeEventListener("resize",e)}),B(()=>{this.props.letter&&!this.dragInitialized&&this.attachListeners()}),k(e=>{this.dragInitialized&&!e.letter&&this.detachListeners()}),P(()=>{this.props.letter&&!this.dragInitialized&&this.attachListeners()}),T(()=>this.detachListeners())}computeContainerSize(){const e=this.infoHeader.el,a=this.contentContainer.el;if(!e||!a)return;const d=window.innerHeight-e.clientHeight;a.style.height=`${d}px`}attachListeners(){this.computeContainerSize(),this.letterPanel.el&&(this.panelDrag.el.addEventListener("mousedown",this.onMouseDown,!1),document.addEventListener("mouseup",this.onMouseUp,!1),this.dragInitialized=!0)}detachListeners(){if(this.letterPanel.el){const e=this.letterPanel.el;e.removeEventListener("mousedown",this.onMouseDown),e.removeEventListener("mouseup",this.onMouseUp),this.dragInitialized=!1}}resize(e){const a=this.dx-e.clientX;this.dx=e.x;const d=this.letterPanel.el,i=this.panelDrag.el;i.style.left=i.offsetLeft-a+"px",d.style.width=`${i.offsetLeft+i.clientWidth}px`}}t(m,"template",u`
    <div class="h-full relative">
      <SignalProblem active="state.signalProblemModal" letterId="props.letterId" onClose="() => state.signalProblemModal = false" />
      <t t-slot="unsafe" />
      <div t-if="props.letter and !currentTranslator.loading" class="flex h-full">
        <div class="h-full relative bg-blue-300 w-2/5" t-ref="letterPanel">
          <div class="shadow-sm overflow-hidden h-full border-gray-400 flex group">
            <div class="w-full h-full relative" id="letter-viewer">
              <t t-if="state.active === false and state.mode === 'letter'">
                <iframe t-att-src="props.letter.pdfUrl" class="w-full h-full" />
              </t>
              <div t-elif="state.mode === 'source'" class="w-full h-full bg-slate-600 py-4 px-5">
                <h3 class="font-semibold text-slate-100 text-2xl">Source Text to translate</h3>
                <h4 class="text-slate-200 max-w-xl mt-3 mb-5 text-sm">Text might not be available, in this case, and if the letter is unavailable too, please contact Compassion by signaling a problem.</h4>
                <div t-foreach="props.letter.translatedElements" t-as="element" t-key="element.id">
                  <t t-if="element.readonly">
                    <div t-if="element.type === 'paragraph'" class="bg-slate-300 p-4 mb-2 rounded-sm shadow">
                      <p t-esc="element.source" class="text-slate-900 text-sm" />
                    </div>
                    <div t-if="element.type === 'pageBreak'" class="bg-slate-400 mb-2 rounded-sm text-slate-100 text-xs flex justify-center py-3">Page Break</div>
                  </t>
                </div>
              </div>
              <div class="flex justify-center w-full absolute top-0">
                <div class="flex gap-2 p-2 bg-white shadow-xl -mt-12 group-hover:mt-0 transition-all">
                  <Button size="'sm'" level="'secondary'" onClick="() => this.state.mode = 'letter'" disabled="state.mode === 'letter'">Letter</Button>
                  <Button size="'sm'" level="'secondary'" onClick="() => this.state.mode = 'source'" disabled="state.mode === 'source'">Source</Button>
                </div>
              </div> 
            </div>
            <div class="w-2 h-full" />
            <div t-ref="panelDrag" class="absolute right-0 w-2 h-full bg-slate-400 z-30 hover:bg-compassion cursor-ew-resize select-none letter-viewer-dragger" />
          </div>
        </div>
        <div class="flex-1 flex flex-col relative">
          <t t-slot="right-pane" />
          <div class="flex-1 w-full flex flex-col relative">
            <div t-ref="header">
              <LetterInformationHeader letter="props.letter" loading="props.smallLoading">
                <t t-slot="action-buttons" letter="props.letter" />
              </LetterInformationHeader>        
            </div>
            <div class="flex-1 relative bg-slate-200">
              <div class="absolute top-0 w-full h-4 bg-gradient-to-b from-slate-300 to-transparent z-10" />
              <div class="overflow-auto py-4" t-ref="contentContainer" id="letter-viewer-content">
                <t t-slot="content" letter="props.letter" />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div t-elif="!props.loading" class="w-full h-full flex flex-col items-center justify-center">
        <Icon icon="'triangle-exclamation'" class="'text-slate-400 text-6xl mb-4'" />
        <p class="text-slate-600 font-semibold mb-2">This letter could not be found</p>
        <div class="flex gap-3">
          <Button color="'red'" level="'secondary'" onClick="() => state.signalProblemModal = true" size="'sm'">Signal a Problem</Button>
          <RouterLink to="'/letters'">
            <Button level="'secondary'" size="'sm'">Back to Translations</Button>
          </RouterLink>
        </div>
      </div>
      <Transition t-slot-scope="scope" active="props.loading or currentTranslator.loading">
        <div class="absolute z-40 bg-slate-200 flex justify-center items-center flex-col top-0 left-0 w-full h-full" t-att-class="scope.itemClass">
          <Loader class="'text-4xl'" />
        </div>
      </Transition>
    </div>
  `),t(m,"props",S),t(m,"components",{Icon:z,RouterLink:L,Transition:C,Loader:g,Button:h,LetterInformationHeader:n,SignalProblem:r});export{m as L,r as S};
