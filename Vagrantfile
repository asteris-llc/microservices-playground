# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"
NUM_HOSTS = 3

def hostname(id)
  "node#{id}"
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "chef/centos-7.0"
  config.ssh.forward_agent = true
  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", "512"]
  end

  # the following enables ansible parallelism by relying on the old insecure
  # shared key model, instead of generating a key for each new host. There may
  # be a way around it (TODO)
  config.ssh.insert_key = false

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "vagrant_playbook.yml"
    ansible.groups = {
      "vagrant" => (1..NUM_HOSTS).collect { |id| hostname(id) }
    }
    ansible.extra_vars = {
      "consul_gossip_key" => "ggVIrhEzqe7W/65YZ9fYFA==",
      "consul_dc" => "vagrant",
      "consul_bootstrap_expect" => 1,
      "consul_retry_join" => 1
    }
  end

  NUM_HOSTS.times do |n|
    id = n + 1
    config.vm.define hostname(id), primary: id == 1 do |host|
      host.vm.network :private_network, ip: "10.0.33.1#{id}"
    end
  end
end
