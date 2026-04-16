  HAOS VM gives you:                                                                                                                                                                                                                           - The exact environment your users will have
  - Full HACS install flow (the real one, not a workaround)                                                                                                                                                                                    - Supervisor, Add-on store, proper restart/reload behavior
  - Snapshot support — take a snapshot of a clean configured state, restore it anytime you want a fresh slate
  - Tests the actual HACS submission flow end-to-end

  The snapshot feature is your "clean image" — much more flexible than a VM snapshot since it's HA-native and includes config, not just disk state.

  ---
  Setup:
  1. Download Home Assistant OS .vmdk for your hypervisor from the HA website
  2. Hyper-V is already on your Windows 11 Pro — no need to install VirtualBox
  3. The HA site has a specific Hyper-V guide with pre-built .vhdx image

  Recommended specs for the VM:
  - 2 vCPUs
  - 4 GB RAM
  - 32 GB disk (the image is small, HA grows over time)
  - Network: Bridged — critical so HA can see your Väinö Pi on the same network

  ---
  Go to home-assistant.io/installation/windows and grab the Hyper-V image. Once it's running and you've completed the onboarding, come back and we'll wire up the dev workflow.



  ● Yes — Phase 5 needs a running HA instance to:

  - Verify the integration loads without errors                                                                                                                                                                                                - Test the config flow UI end-to-end
  - Confirm all entities appear correctly under the Väinö device                                                                                                                                                                               - Catch any import or runtime errors before HACS submission

  HACS reviewers will reject integrations that don't load cleanly, so we want to shake out any issues before submitting.

  Go ahead and reboot. Once HAOS is up and you've completed the initial HA onboarding, come back and we'll:

  1. Copy custom_components/vaino/ into the HA config directory
  2. Add the integration via the UI
  3. Point it at your Väinö Pi
  4. Fix anything that surfaces
  5. Then write the tests and submit to HACS


  claude --resume fb7912fb-296c-4f83-aef5-db2c85d3bf49 --dangerously-skip-permissions

  
  
  HAOS IP: 192.168.5.250
  
http://haos-viano.local:8123
