  var app = new Vue({
    el: '#app',
    delimiters: ['{', '}'],
    data: {
      json: null,
      packages: null,
      inhouseguests: null,
      guestpackages: null,
      showpackagelist: true,
      activepackages: [],
      refreshingnow: false,
      checkbodytemp: true,
      shownguests: [],
      consumed: [],
      dark: true,
      todaydate: 'сегодня',
      value: 50
    },
    created: function() {

       this.refresh();
    },

    methods: {
      refresh: function() {
        this.refreshingnow = true;
        axios.get("inhouselist/api/get").then(response => {
          this.json = response;
          this.todaydate = this.json.data.date.toString();
          this.packages = this.json.data.packages;
          this.inhouseguests = this.json.data.inhouseguests;
          this.guestpackages = this.json.data.guestpackages;
          this.refreshingnow = false;
         });
      },

      scrollToTop() {
                window.scrollTo(0,0);
      },

      addremoveactivepackage: function(pacid) {
        if (!this.activepackages.includes(pacid)) {
          this.activepackages.unshift(pacid);
        }
        else {this.activepackages = this.activepackages.filter(item => item != pacid);}
        this.updateguestlist();
      },

      updateguestlist: function() {
        this.shownguests = [];
        for (var i = 0; i < this.inhouseguests.length; i++){
          for (var n = 0; n < this.guestpackages.length; n++) {
            if (this.activepackages.includes(this.guestpackages[n].ypac_id)
              &&  this.guestpackages[n].ydet_id == this.inhouseguests[i].ydet_id
              && !this.consumed.includes(this.guestpackages[n].ypal_id)) {
              this.shownguests.unshift(this.inhouseguests[i].ydet_id);
          }
        }     
      }},
      getpackagename: function(pacid) {
        for(var i = 0; i < this.packages.length; i++) {
          if (this.packages[i].ypac_id == pacid) {
            return(this.packages[i].longdesc);
            break;
          }
        }
      },
      showpackage: function(itemydetid, linkydetid, linkypacid) {
        if(itemydetid == linkydetid && this.activepackages.includes(linkypacid)) {
          return(true);
        } else {
          return(false);
        }
      },
      consume: function(palid, bodytemp) {
        this.refreshingnow = true;
        axios.put("/inhouselist/api/put", {palid : palid.toString(), bodytemp: bodytemp.toString()}, {headers: {"Content-Type": "text/plain"}})
        .then((response) => {
          this.refreshingnow = false;
          this.consumed.unshift(palid);
          this.updateguestlist();
        })
        .catch((error) => {
          console.log(error);
        });

    }
  }});



