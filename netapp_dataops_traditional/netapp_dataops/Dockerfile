FROM alpine:latest


# install ansible
RUN apk --update --no-cache add ansible

# upgrade pip
RUN apk --update --no-cache add py3-pip

#install pandas and numpy
RUN apk add --update --no-cache openssh

#install pandas and numpy
RUN apk add --update --no-cache py3-numpy py3-pandas

#install build tools
RUN apk add --update --no-cache make automake gcc g++ subversion python3-dev

#install netapp ansible coolection from galaxy 
RUN ansible-galaxy collection install netapp.ontap -p /usr/share/ansible/collections
RUN ansible-galaxy collection install netapp.elementsw -p /usr/share/ansible/collections
RUN ansible-galaxy collection install netapp.storagegrid -p /usr/share/ansible/collections
RUN ansible-galaxy collection install netapp.um_info -p /usr/share/ansible/collections

RUN python3 -m pip install netapp-dataops-traditional
