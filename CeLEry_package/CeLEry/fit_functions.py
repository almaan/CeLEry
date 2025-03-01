import random
import numpy as np
import pandas as pd
import torch
import os

from . datasetgenemap import wrap_gene_location
from . datasetgenemap import wrap_gene_layer
from . datasetgenemap import wrap_gene_domain
from . DNN import DNN
from . DNN import DNN5
from . DNN import DNNordinal
from . DNN import DNNdomain
from . DNN import DNNregion
from . util_Mouse import report_region

from . TrainerExe import TrainerExe
import pickle

from scipy.sparse import issparse

import warnings
# warnings.filterwarnings('ignore',lineno='.*Trying to modify attribute.*')

def seed_worker(worker_id):
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)

def Fit_cord (data_train, location_data = None, hidden_dims = [30, 25, 15], num_epochs_max = 500, path = "", filename = "PreOrg_Mousesc", batch_size = 4, num_workers = 1, number_error_try = 15, initial_learning_rate = 0.0001, seednum = 2021, save_model = False,):
    #
    random.seed(seednum)
    torch.manual_seed(seednum)
    np.random.seed(seednum)
    g = torch.Generator()
    g.manual_seed(seednum)
    #
    if location_data is None:
        location_data = data_train.obs
    #
    traindata = (data_train.X.A if issparse(data_train.X) else data_train.X)
    tdatax = np.expand_dims(traindata, axis = 0)
    tdata_rs = np.swapaxes(tdatax, 1, 2)
    DataTra = wrap_gene_location(tdata_rs, location_data)
    t_loader= torch.utils.data.DataLoader(DataTra, batch_size=batch_size, num_workers = num_workers, shuffle = True, worker_init_fn=seed_worker, generator=g)
    # Create Deep Neural Network for Coordinate Regression
    if len(hidden_dims) == 5:
        DNNmodel = DNN5( in_channels = DataTra[1][0].shape[0], hidden_dims = hidden_dims) # [100,50,25] )
    else:
        DNNmodel = DNN( in_channels = DataTra[1][0].shape[0], hidden_dims = hidden_dims) # [100,50,25] )
    DNNmodel = DNNmodel.float()
    #
    CoOrg = TrainerExe()
    CoOrg.train(model = DNNmodel, train_loader = t_loader, num_epochs= num_epochs_max, RCcountMax = number_error_try, learning_rate = initial_learning_rate)
    #
    if save_model:
        try:
            os.makedirs("{path}".format(path = path))
        except FileExistsError:
            print("Folder already exists")
        filename3 = "{path}/{filename}.obj".format(path = path, filename = filename) #"../output/CeLEry/Mousesc/PreOrg_Mousesc.obj"
        filehandler2 = open(filename3, 'wb') 
        pickle.dump(DNNmodel, filehandler2)

    return DNNmodel


def Fit_region (data_train, alpha = 0.95, location_data = None, hidden_dims = [30, 25, 15], num_epochs_max = 500, path = "", filename = "PreOrg_Mousesc", batch_size = 4, num_workers = 1, number_error_try = 15, initial_learning_rate = 0.0001, seednum = 2021):
    #
    random.seed(seednum)
    torch.manual_seed(seednum)
    np.random.seed(seednum)
    g = torch.Generator()
    g.manual_seed(seednum)
    #
    if location_data is None:
        location_data = data_train.obs
    #
    traindata = (data_train.X.A if issparse(data_train.X) else data_train.X)
    tdatax = np.expand_dims(traindata, axis = 0)
    tdata_rs = np.swapaxes(tdatax, 1, 2)
    DataTra = wrap_gene_location(tdata_rs, location_data)
    t_loader= torch.utils.data.DataLoader(DataTra, batch_size=batch_size, num_workers = num_workers, shuffle = True, worker_init_fn=seed_worker, generator=g)
    # Create Deep Neural Network for Coordinate Regression
    DNNmodel = DNNregion( in_channels = DataTra[1][0].shape[0], alpha = alpha,  hidden_dims = hidden_dims) # [100,50,25] )
    DNNmodel = DNNmodel.float()
    #
    CoOrg = TrainerExe()
    CoOrg.train(model = DNNmodel, train_loader = t_loader, num_epochs= num_epochs_max, RCcountMax = number_error_try, learning_rate = initial_learning_rate)
    #
    try:
        os.makedirs("{path}".format(path = path))
    except FileExistsError:
        print("Folder already exists")
    filename3 = "{path}/{filename}.obj".format(path = path, filename = filename) #"../output/CeLEry/Mousesc/PreOrg_Mousesc.obj"
    filehandler2 = open(filename3, 'wb') 
    pickle.dump(DNNmodel, filehandler2)
    return DNNmodel    

def Fit_layer (data_train, layer_weights, layer_data = None, layerkey = "layer", hidden_dims = [10, 5, 2], num_epochs_max = 500, path = "", filename = "PreOrg_layersc", batch_size = 4, num_workers = 1, number_error_try = 15, initial_learning_rate = 0.0001, seednum = 2021):
    #
    random.seed(seednum)
    torch.manual_seed(seednum)
    np.random.seed(seednum)
    g = torch.Generator()
    g.manual_seed(seednum)
    #
    if layer_data is None:
        layer_data = data_train.obs
    #
    layer_weights = torch.tensor(layer_weights.to_numpy())
    traindata = (data_train.X.A if issparse(data_train.X) else data_train.X)
    tdatax = np.expand_dims(traindata, axis = 0)
    tdata_rs = np.swapaxes(tdatax, 1, 2)
    DataTra = wrap_gene_layer(tdata_rs, layer_data, layerkey)
    t_loader= torch.utils.data.DataLoader(DataTra, batch_size = batch_size, num_workers = num_workers, shuffle = True, worker_init_fn=seed_worker, generator=g)
    # Create Deep Neural Network for Coordinate Regression
    DNNmodel = DNNordinal( in_channels = DataTra[1][0].shape[0], num_classes = layer_weights.shape[0], hidden_dims = hidden_dims, importance_weights = layer_weights) # [100,50,25] )
    DNNmodel = DNNmodel.float()
    #
    CoOrg= TrainerExe()
    CoOrg.train(model = DNNmodel, train_loader = t_loader, num_epochs= num_epochs_max, RCcountMax = number_error_try, learning_rate = initial_learning_rate)
    #
    filename3 = "{path}/{filename}.obj".format(path = path, filename = filename)
    filehandler2 = open(filename3, 'wb') 
    pickle.dump(DNNmodel, filehandler2)

def Fit_domain (data_train, domain_weights, domain_data = None, domainkey = "layer", hidden_dims = [10, 5, 2], num_epochs_max = 500, path = "", filename = "PreOrg_domainsc", batch_size = 4, num_workers = 1, number_error_try = 15, initial_learning_rate = 0.0001, seednum = 2021):
    #
    random.seed(seednum)
    torch.manual_seed(seednum)
    np.random.seed(seednum)
    g = torch.Generator()
    g.manual_seed(seednum)
    #
    if domain_data is None:
        domain_data = data_train.obs
    #
    domain_weights = torch.tensor(domain_weights.to_numpy(), dtype=torch.float32)
    traindata = (data_train.X.A if issparse(data_train.X) else data_train.X)
    tdatax = np.expand_dims(traindata, axis = 0)
    tdata_rs = np.swapaxes(tdatax, 1, 2)
    DataTra = wrap_gene_domain(tdata_rs, domain_data, domainkey)
    t_loader= torch.utils.data.DataLoader(DataTra, batch_size = batch_size, num_workers = num_workers, shuffle = True, worker_init_fn=seed_worker, generator=g)
    # Create Deep Neural Network for Coordinate Regression
    DNNmodel = DNNdomain( in_channels = DataTra[1][0].shape[0], num_classes = domain_weights.shape[0], hidden_dims = hidden_dims, importance_weights = domain_weights) # [100,50,25] )
    DNNmodel = DNNmodel.float()
    #
    CoOrg= TrainerExe()
    CoOrg.train(model = DNNmodel, train_loader = t_loader, num_epochs= num_epochs_max, RCcountMax = number_error_try, learning_rate = initial_learning_rate)
    #
    filename3 = "{path}/{filename}.obj".format(path = path, filename = filename)
    filehandler2 = open(filename3, 'wb') 
    pickle.dump(DNNmodel, filehandler2)

def Predict_cord (data_test, model = None, path = None, filename = None, location_data = None, save_pred = False):
    testdata= (data_test.X.A if issparse(data_test.X) else data_test.X)
    if location_data is None:
        location_data = pd.DataFrame(np.ones((data_test.shape[0],2)), columns = ["psudo1", "psudo2"])
    ## Wrap up Validation data in to dataloader
    vdatax = np.expand_dims(testdata, axis = 0)
    vdata_rs = np.swapaxes(vdatax, 1, 2)
    DataVal = wrap_gene_location(vdata_rs, location_data)
    Val_loader= torch.utils.data.DataLoader(DataVal, batch_size=1, num_workers = 1)
    
    #
    cord = report_prop_method_sc(Val_loader,DNNmodel = model, folder = path,
                        name = filename, data_test = data_test, save_pred = False,
                        )
    data_test.obs["x_cord_pred"] = cord[:,0]
    data_test.obs["y_cord_pred"] = cord[:,1]
    return cord


def report_prop_method_sc (Val_loader, DNNmodel = None, folder = None, name = None, data_test = None,outname = None, save_pred = False):
    """
        Report the results of the proposed methods in comparison to the other method
        :folder: string: specified the folder that keep the proposed DNN method
        :name: string: specified the name of the DNN method, also will be used to name the output files
        :data_test: AnnData: the data of query data
        :Val_loader: Dataload: the validation data from dataloader
        :outname: string: specified the name of the output, default is the same as the name
    """
    if DNNmodel is None:
	    filename2 = "{folder}/{name}.obj".format(folder = folder, name = name)
	    filehandler = open(filename2, 'rb') 
	    DNNmodel = pickle.load(filehandler)

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    DNNmodel = DNNmodel.to(device)
    #
    coords_predict = np.zeros((data_test.obs.shape[0],2))
    #
    for i, img in enumerate(Val_loader):
        img[0] = img[0].to(device)
        recon = DNNmodel(img)
        coords_predict[i,:] = recon[0].cpu().detach().numpy()
    if save_pred:
        np.savetxt("{folder}/{name}_predmatrix.csv".format(folder = folder, name = name), coords_predict, delimiter=",")

    return coords_predict



def Predict_region (data_test, path = "", filename = "PreOrg_ConfScore", location_data = None, hist = ""):
    testdata= (data_test.X.A if issparse(data_test.X) else data_test.X)
    if location_data is None:
        location_data = pd.DataFrame(np.ones((data_test.shape[0],2)), columns = ["psudo1", "psudo2"])
    ## Wrap up Validation data in to dataloader
    vdatax = np.expand_dims(testdata, axis = 0)
    vdata_rs = np.swapaxes(vdatax, 1, 2)
    DataVal = wrap_gene_location(vdata_rs, location_data)
    Val_loader= torch.utils.data.DataLoader(DataVal, batch_size=1, num_workers = 1)
    #
    [losstotal, area_record] = report_region(folder = path,
                        name = filename, data_test = data_test,
                        Val_loader = Val_loader, hist = hist)
    conf_score = [1-i for i in area_record]
    data_test.obs["area_record"] = np.array(area_record)
    data_test.obs["conf_score"] = np.array(conf_score)
    return losstotal


def Predict_domain (data_test, class_num,  path = "", filename = "PreOrg_domainsc", truth_label = None, predtype = "probabilistic"):
    if truth_label is None:
        truth_label = "psudo_label"
        location_data = pd.DataFrame(np.ones((data_test.shape[0],1)), columns = ["psudo_label"])
    ## Wrap up Validation data in to dataloader
    testdata = (data_test.X.A if issparse(data_test.X) else data_test.X)
    vdatax = np.expand_dims(testdata, axis = 0)
    vdata_rs = np.swapaxes(vdatax, 1, 2)
    DataVal = wrap_gene_domain(vdata_rs, location_data, truth_label)
    Val_loader= torch.utils.data.DataLoader(DataVal, batch_size=1, num_workers = 1)
    #
    domain = report_prop_method_domain(folder = path,
                       name = filename,
                       data_test = data_test,
                       Val_loader = Val_loader,
                       class_num = class_num)
    data_test.obs["domain_cel_pred"] = domain[1]
    if predtype == "probabilistic":
        return domain[0]
    elif predtype == "deterministic":
        return domain[1]
    return domain


def report_prop_method_domain (folder, name, data_test, Val_loader, class_num):
    """
        Report the results of the proposed methods in comparison to the other method
        :folder: string: specified the folder that keep the proposed DNN method
        :name: string: specified the name of the DNN method, also will be used to name the output files
        :data_test: AnnData: the data of query data
        :Val_loader: Dataload: the validation data from dataloader
        :class_num: int: the number of classes
        :predtype: string: if the prediction type is "probality", then a probability matrix will returned. Otherwise a deterministic will returned.
    """
    filename2 = "{folder}/{name}.obj".format(folder = folder, name = name)
    filehandler = open(filename2, 'rb') 
    DNNmodel = pickle.load(filehandler)
    #
    coords_predict = np.zeros(data_test.obs.shape[0])
    payer_prob = np.zeros((data_test.obs.shape[0],class_num+1))
    for i, img in enumerate(Val_loader):
        recon = DNNmodel(img)
        logitsvalue = np.squeeze(torch.exp(recon[0]).detach().numpy(), axis = 0)
        prbfull = logitsvalue / sum(logitsvalue)
        prbfull = np.nan_to_num(prbfull, nan=1.0)
        coords_predict[i] = np.where(prbfull == prbfull.max())[0].max()
        payer_prob[i,1:] = prbfull
    #
    data_test.obs["pred_domain"] = coords_predict.astype(int)
    data_test.obs["pred_domain_str"] = coords_predict.astype(int).astype('str')
    payer_prob[:,0] = data_test.obs["pred_domain"]
    np.savetxt("{folder}/{name}_probmat.csv".format(folder = folder, name = name), payer_prob, delimiter=',')
    return [payer_prob[:,1:], coords_predict]


def report_prop_method_layer (folder, name, data_test, Val_loader, class_num):
    """
        Report the results of the proposed methods in comparison to the other method
        :folder: string: specified the folder that keep the proposed DNN method
        :name: string: specified the name of the DNN method, also will be used to name the output files
        :dataSection2: AnnData: the data of Section 2
        :traindata: AnnData: the data used in training data. This is only needed for compute SSIM
        :Val_loader: Dataload: the validation data from dataloader
        :outname: string: specified the name of the output, default is the same as the name
        :ImageSec2: Numpy: the image data that are refering to
    """
    filename2 = "{folder}/{name}.obj".format(folder = folder, name = name)
    filehandler = open(filename2, 'rb') 
    DNNmodel = pickle.load(filehandler)
    #
    coords_predict = np.zeros(data_test.obs.shape[0])
    payer_prob = np.zeros((data_test.obs.shape[0],class_num+1))
    for i, img in enumerate(Val_loader):
        recon = DNNmodel(img)
        logitsvalue = np.squeeze(torch.sigmoid(recon[0]).detach().numpy(), axis = 0)
        if (logitsvalue[class_num-2] == 1):
            coords_predict[i] = class_num
            payer_prob[i,class_num] = 1
        else:
            logitsvalue_min = np.insert(logitsvalue, 0, 1, axis=0)
            logitsvalue_max = np.insert(logitsvalue_min, class_num, 0, axis=0) 
            prb = np.diff(logitsvalue_max)
            prbfull = -prb.copy() 
            coords_predict[i] = np.where(prbfull == prbfull.max())[0].max() + 1
            payer_prob[i,1:] = prbfull
    #
    data_test.obs["pred_layer"] = coords_predict.astype(int)
    payer_prob[:,0] =  data_test.obs["pred_layer"]
    data_test.obs["pred_layer_str"] = coords_predict.astype(int).astype('str')
    np.savetxt("{folder}/{name}_probmat.csv".format(folder = folder, name = name), payer_prob, delimiter=',')
    return [payer_prob[:,1:], coords_predict]

def Predict_layer (data_test, class_num,  path = "", filename = "PreOrg_layernsc", truth_label = None, predtype = "probabilistic"):
    if truth_label is None:
        truth_label = "psudo_label"
        location_data = pd.DataFrame(np.ones((data_test.shape[0],1)), columns = ["psudo_label"])
        location_data.iloc[0] = 2
    ## Wrap up Validation data in to dataloader
    testdata = (data_test.X.A if issparse(data_test.X) else data_test.X)
    vdatax = np.expand_dims(testdata, axis = 0)
    vdata_rs = np.swapaxes(vdatax, 1, 2)
    DataVal = wrap_gene_layer(vdata_rs, location_data, layerkey = truth_label)
    Val_loader= torch.utils.data.DataLoader(DataVal, batch_size=1, num_workers = 1)
    #
    domain = report_prop_method_layer(folder = path,
                       name = filename,
                       data_test = data_test,
                       Val_loader = Val_loader,
                       class_num = class_num)
    data_test.obs["layer_cel_pred"] = domain[1]
    if predtype == "probabilistic":
        return domain[0]
    elif predtype == "deterministic":
        return domain[1]
    return domain
