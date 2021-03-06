#!/usr/bin/env python3
# Copyright (c) 2017 The Particl Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from test_framework.test_particl import ParticlTestFramework
from test_framework.test_particl import isclose
from test_framework.util import *


class SmsgPaidTest(ParticlTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.extra_args = [ ['-debug','-noacceptnonstdtxn'] for i in range(self.num_nodes) ]

    def setup_network(self, split=False):
        self.add_nodes(self.num_nodes, extra_args=self.extra_args)
        self.start_nodes()
        connect_nodes(self.nodes[0], 1)

        self.is_network_split = False
        self.sync_all()


    def run_test (self):
        tmpdir = self.options.tmpdir
        nodes = self.nodes

        # Stop staking
        for i in range(len(nodes)):
            nodes[i].reservebalance(True, 10000000)

        nodes[0].extkeyimportmaster(nodes[0].mnemonic('new')['master'])
        nodes[1].extkeyimportmaster('abandon baby cabbage dad eager fabric gadget habit ice kangaroo lab absorb')

        address0 = nodes[0].getnewaddress() # will be different each run
        address1 = nodes[1].getnewaddress()
        assert(address1 == 'pX9N6S76ZtA5BfsiJmqBbjaEgLMHpt58it')

        ro = nodes[0].smsglocalkeys()
        assert(len(ro['wallet_keys']) == 0)

        ro = nodes[0].smsgaddlocaladdress(address0)
        assert('Receiving messages enabled for address' in ro['result'])

        ro = nodes[0].smsglocalkeys()
        assert(len(ro['wallet_keys']) == 1)


        ro = nodes[1].smsgaddaddress(address0, ro['wallet_keys'][0]['public_key'])
        assert(ro['result'] == 'Public key added to db.')

        text_1 = "['data':'test','value':1]"
        ro = nodes[1].smsgsend(address1, address0, text_1, True, 4, True)
        assert(ro['result'] == 'Not Sent.')
        assert(isclose(ro['fee'], 0.00085800))


        ro = nodes[1].smsgsend(address1, address0, text_1, True, 4)
        assert(ro['result'] == 'Sent.')

        self.stakeBlocks(1, nStakeNode=1)
        self.waitForSmsgExchange(1, 1, 0)

        ro = nodes[0].smsginbox()
        assert(len(ro['messages']) == 1)
        assert(ro['messages'][0]['text'] == text_1)


        ro = nodes[0].smsgimportprivkey('7pHSJFY1tNwi6d68UttGzB8YnXq2wFWrBVoadLv4Y6ekJD3L1iKs', 'smsg test key')

        address0_1 = 'pasdoMwEn35xQUXFvsChWAQjuG8rEKJQW9'
        text_2 = "['data':'test','value':2]"
        ro = nodes[0].smsglocalkeys()
        assert(len(ro['smsg_keys']) == 1)
        assert(ro['smsg_keys'][0]['address'] == address0_1)

        ro = nodes[1].smsgaddaddress(address0_1, ro['smsg_keys'][0]['public_key'])
        assert(ro['result'] == 'Public key added to db.')

        ro = nodes[1].smsgsend(address1, address0_1, text_2, True, 4)
        assert(ro['result'] == 'Sent.')

        self.stakeBlocks(1, nStakeNode=1)
        self.waitForSmsgExchange(2, 1, 0)

        ro = nodes[0].smsginbox()
        assert(len(ro['messages']) == 1)
        assert(ro['messages'][0]['text'] == text_2)



        ro = nodes[0].encryptwallet("qwerty234")
        assert("wallet encrypted" in ro)

        nodes[0].wait_until_stopped() # wait until encryptwallet has shut down node
        self.start_node(0, self.extra_args[0])
        connect_nodes(self.nodes[0], 1)
        connect_nodes(self.nodes[0], 2)
        ro = nodes[0].getwalletinfo()
        assert(ro['encryptionstatus'] == 'Locked')

        localkeys0 = nodes[0].smsglocalkeys()
        assert(len(localkeys0['smsg_keys']) == 1)
        assert(len(localkeys0['wallet_keys']) == 1)
        assert(localkeys0['smsg_keys'][0]['address'] == address0_1)
        assert(localkeys0['wallet_keys'][0]['address'] == address0)

        text_3 = "['data':'test','value':3]"
        ro = nodes[0].smsglocalkeys()
        assert(len(ro['smsg_keys']) == 1)
        assert(ro['smsg_keys'][0]['address'] == address0_1)

        ro = nodes[1].smsgsend(address1, address0, 'Non paid msg')
        assert(ro['result'] == 'Sent.')

        ro = nodes[1].smsgsend(address1, address0_1, text_3, True, 4)
        assert(ro['result'] == 'Sent.')
        assert(len(ro['txid']) == 64)

        self.sync_all()
        self.stakeBlocks(1, nStakeNode=1)
        self.waitForSmsgExchange(4, 1, 0)

        ro = nodes[0].walletpassphrase("qwerty234", 300)
        ro = nodes[0].smsginbox()
        assert(len(ro['messages']) == 2)
        flat = json.dumps(ro, default=self.jsonDecimal)
        assert('Non paid msg' in flat)
        assert(text_3 in flat)

        ro = nodes[0].walletlock()

        ro = nodes[0].smsginbox("all")
        assert(len(ro['messages']) == 4)
        flat = json.dumps(ro, default=self.jsonDecimal)
        assert(flat.count('Wallet is locked') == 2)


        #assert(False)
        #print(json.dumps(ro, indent=4, default=self.jsonDecimal))

if __name__ == '__main__':
    SmsgPaidTest().main()
