### RUN THESE LINES IN IPYTHON NOTEBOOK TO BRING UP UI
### execfile('run_ui.py')
### resp = run_ui()
### HTML(resp)


### You can run any existing function by importing and running on the click of the javascript popup

from IPython.display import HTML

def run_ui():
    html_str = """
     
    <p>
     <label><b>Type</b></label>
     <select id="QAnswer">
       <option value = "exact_domain">Exact Domain</option>
       <option value = "rebrand">Rebrand</option>
       <option value = "international">International</option>
       <option value = "subsidiary_brand">Subsidiary Brand</option>
       <option value = "subsidiary_product">Subsidiary Product</option>
     </select>
    </p>
    
    <p>
     <label><b>API Key</b></label>
     <select id="api_key">
       <option value = "blahblah">Courtney</option>
       <option value = "blahblah2">KLiu</option>
       <option value = "blahblah3">JLux</option>
     </select>
    </p>
    
    <p>
        <form><b><b>
          Dominant Company:<br>
          <input type="text" id="company_new" placeholder="1234567"><br>
          Recessive Company:<br>
          <input type="text" id="company_old" placeholder="1234567"><br>
          Twitter Date:<br>
          <input type="text" id="twitter_date" placeholder="(2015,1,30)"><br>
          Facebook Date:<br>
          <input type="text" id="facebook_date" placeholder="(2015,1,30)"><br>
          Alexa Date:<br>
          <input type="text" id="alexa_date" placeholder="(2015,1,30)"><br>
        </form>
    <p><br></p><button id="set-value-button">Set And Run</button>


    <script type="text/Javascript">

        $("button#set-value-button").click(function(event) {
            event.preventDefault();
            window.confirm("ARE YOU SURE YOU WANT TO RUN THIS?");
            var kernel = IPython.notebook.kernel;
            var company_new = $('#company_new').val();
            kernel.execute('company_new='+company_new);
            var company_old = $('#company_old').val();
            kernel.execute('company_old='+company_old);
            var twitter_date = $('#twitter_date').val();
            kernel.execute("twitter_date="+twitter_date);
            var facebook_date = $('#facebook_date').val();
            kernel.execute("facebook_date="+facebook_date);
            var alexa_date = $('#alexa_date').val();
            kernel.execute("alexa_date="+alexa_date);
            var merge_type = $('#QAnswer').val();
            kernel.execute('merge_type="'+merge_type+'"');
            var api_key = $('#api_key').val();
            kernel.execute('api_key="'+api_key+'"');
            
        });
    </script>
    """
    return html_str
