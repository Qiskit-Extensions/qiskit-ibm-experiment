# Qiskit IBM Experiment service

**Qiskit** is an open-source SDK for working with quantum computers at the level of circuits, algorithms, and application modules.

This project contains a service that allows accessing the **[IBM Quantum]**
experiment database.

## Installation
The provider can be installed via pip:

```bash
pip install qiskit-ibm-experiment
```

## Provider Setup

1. Create an IBM Quantum account or log in to your existing account by visiting the [IBM Quantum login page].

2. Ensure you have access to the experiment database.

3. Copy (and/or optionally regenerate) your API token from your
   [IBM Quantum account page].

4. Take your token from step 2, here called `MY_API_TOKEN`, and save it by calling `IBMExperimentService.save_account()`:

   ```python
   from qiskit_ibm_experiment import IBMExperimentService
   IBMExperimentService.save_account(token='MY_API_TOKEN')
   ```

   The command above stores your credentials locally in a configuration file called `qiskit-ibm.json`. By default, this file is located in `$HOME/.qiskit`, where `$HOME` is your home directory.
   
   Once saved you can then instantiate the experiment service without using the API token:

   ```python
   from qiskit_ibm_experiment import IBMExperimentService
   service = IBMExperimentService()

   # display current supported backends
   print(service.backends())

   # get the latest experiments in the DB
   experiment_list = service.experiments()
   ```
   
   You can also save specific configuration under a given name:
   
   ```python
   from qiskit_ibm_experiment import IBMExperimentService
   IBMExperimentService.save_account(name='my_config', token='MY_API_TOKEN')
   ```
   
   And explicitly load it:
   ```python
   from qiskit_ibm_experiment import IBMExperimentService
   service = IBMExperimentService(name='my_config')

   # display current supported backends
   print(service.backends())

### Load Account from Environment Variables
Alternatively, the IBM Provider can discover credentials from environment variables:
```bash
export QISKIT_IBM_EXPERIMENT_TOKEN='MY_API_TOKEN'
export QISKIT_IBM_EXPERIMENT_URL='https://auth.quantum-computing.ibm.com/api'
```

Then instantiate the provider without any arguments and access the backends:
```python
from qiskit_ibm_experiment import IBMExperimentService
service = IBMExperimentService()
```

Environment variable take precedence over the default account saved to disk via `save_account`,
if one exists; but if the `name` parameter is given, the environment variables are ignored.

### Enable Account for Current Session
As another alternative, you can also enable an account just for the current session by instantiating the service with the token

```python
from qiskit_ibm_experiment import IBMExperimentService
service = IBMExperimentService(token='MY_API_TOKEN')
```

## Contribution Guidelines

If you'd like to contribute to IBM Quantum Experiment Service, please take a look at our
[contribution guidelines]. This project adheres to Qiskit's [code of conduct].
By participating, you are expect to uphold to this code.

We use [GitHub issues] for tracking requests and bugs. Please use our [slack]
for discussion and simple questions. To join our Slack community use the
invite link at [Qiskit.org]. For questions that are more suited for a forum we
use the `Qiskit` tag in [Stack Exchange].

## Next Steps

Now you're set up and ready to check out some of the other examples from our
[Qiskit Tutorial] repository.

## Authors and Citation

The Qiskit IBM Quantum Experiment Service is the work of [many people] who contribute to the
project at different levels. If you use Qiskit, please cite as per the included
[BibTeX file].

## License

[Apache License 2.0].

[IBM Quantum]: https://www.ibm.com/quantum-computing/
[IBM Quantum login page]:  https://quantum-computing.ibm.com/login
[IBM Quantum account page]: https://quantum-computing.ibm.com/account
[contribution guidelines]: https://github.com/Qiskit/qiskit-ibm-experiment/blob/main/CONTRIBUTING.md
[code of conduct]: https://github.com/Qiskit/qiskit-ibm-experiment/blob/main/CODE_OF_CONDUCT.md
[GitHub issues]: https://github.com/Qiskit/qiskit-ibm-experiment/issues
[slack]: https://qiskit.slack.com
[Qiskit.org]: https://qiskit.org
[Stack Exchange]: https://quantumcomputing.stackexchange.com/questions/tagged/qiskit
[Qiskit Tutorial]: https://github.com/Qiskit/qiskit-tutorial
[many people]: https://github.com/Qiskit/qiskit-ibm-experiment/graphs/contributors
[BibTeX file]: https://github.com/Qiskit/qiskit/blob/master/Qiskit.bib
[Apache License 2.0]: https://github.com/Qiskit/qiskit-ibm-experiment/blob/main/LICENSE.txt
