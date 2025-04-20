import time, itertools
from dataset import ImageFolder
from torchvision import transforms
from torch.utils.data import DataLoader
from networks import *
from utils import *
from glob import glob
from PIL import Image
from cv2 import resize

class SRDefog(object) :
    def __init__(self, args):        
        self.model_name = 'SRDefog'

        self.result_dir = args.result_dir
        self.dataset = args.dataset
        self.datasetpath = args.datasetpath

        self.batch_size = args.batch_size
        self.ch = args.ch
        self.n_res = args.n_res

        self.img_size = args.img_size
        self.img_h = args.img_h
        self.img_w = args.img_w
        self.img_ch = args.img_ch

        self.device = args.device
        self.im_suf_A = args.im_suf_A
        
        print()

        print("##### Information #####")
        print("# dataset : ", self.dataset)
        print("# datasetpath : ", self.datasetpath)

    def build_model(self):
        self.test_transform = transforms.Compose([
            transforms.Resize((self.img_size, self.img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
        ])
      
        self.testA = ImageFolder(os.path.join('dataset', self.datasetpath), self.test_transform)
        self.testA_loader = DataLoader(self.testA, batch_size=1, shuffle=False)

        self.genA2B = ResnetGenerator(input_nc=3, output_nc=3, ngf=self.ch, n_blocks=self.n_res, img_size=self.img_size, light=True).to(self.device)
        self.genB2A = ResnetGenerator(input_nc=3, output_nc=3, ngf=self.ch, n_blocks=self.n_res, img_size=self.img_size, light=True).to(self.device)
        self.disGA = Discriminator(input_nc=3, ndf=self.ch, n_layers=7).to(self.device)
        self.disGB = Discriminator(input_nc=3, ndf=self.ch, n_layers=7).to(self.device)
        self.disLA = Discriminator(input_nc=3, ndf=self.ch, n_layers=5).to(self.device)
        self.disLB = Discriminator(input_nc=3, ndf=self.ch, n_layers=5).to(self.device)

    def load(self, dir, step):
        params = torch.load(os.path.join(dir, self.dataset + '_params_%07d.pt' % step))
        self.genA2B.load_state_dict(params['genA2B'])
        self.genB2A.load_state_dict(params['genB2A'])
        self.disGA.load_state_dict(params['disGA'])
        self.disGB.load_state_dict(params['disGB'])
        self.disLA.load_state_dict(params['disLA'])
        self.disLB.load_state_dict(params['disLB'])

    def test(self):
        print(os.path.join(self.result_dir, self.dataset, 'model', '*.pt'))
        model_list = glob(os.path.join(self.result_dir, self.dataset, 'model', '*.pt'))
        if not len(model_list) == 0:
            model_list.sort()
            print('model_list',model_list)
            for i in range(-1,0,1):
                iter = int(model_list[i].split('_')[-1].split('.')[0])
                print('iter',iter)
                self.load(os.path.join(self.result_dir, self.dataset, 'model'), iter)
                print(" [*] Load SUCCESS")

                self.genA2B.eval(), self.genB2A.eval()
                 
                path_fakeB=os.path.join(self.result_dir, self.dataset, str(iter)+'/'+'output')
                print(path_fakeB)
                if not os.path.exists(path_fakeB):
                    os.makedirs(path_fakeB)
                    
                self.gt_list = [os.path.splitext(f)[0] for f in os.listdir(os.path.join(self.datasetpath)) if f.endswith(self.im_suf_A)]
                self.gt_list=["C:\\Users\AADHI\\Downloads\\FogRemoval-main\\FogRemoval-main\\test_input\\t2003"]
                print(self.gt_list)
                for n, img_name in enumerate(self.gt_list):
                    print('predicting: %d / %d' % (n + 1, len(self.gt_list)))
                    
                    img = Image.open(os.path.join('dataset', self.datasetpath,  img_name + self.im_suf_A)).convert('RGB')
                    img_width, img_height =img.size
                    
                    real_A = (self.test_transform(img).unsqueeze(0)).to(self.device)                                            
                    fake_A2B, _, _ = self.genA2B(real_A)
                    
                    A_real = RGB2BGR(tensor2numpy(denorm(real_A[0])))
                    B_fake = RGB2BGR(tensor2numpy(denorm(fake_A2B[0])))
                    A_real = resize(A_real, (img_width, img_height))
                    B_fake = resize(B_fake, (img_width, img_height))
                    
                    A2B = np.concatenate((A_real, B_fake), 1)

                    cv2.imwrite(os.path.join(path_fakeB,  '%s_out.png' % img_name), B_fake * 255.0)
                    cv2.imwrite(os.path.join(path_fakeB,  '%s_inout.png' % img_name), A2B * 255.0)

